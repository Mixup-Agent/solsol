"""meta 에이전트 — 다음 면접관을 적응적으로 선택하고 종료를 판단한다."""
import logging
from typing import Literal

from pydantic import BaseModel, Field

from app.agents.helpers import format_transcript
from app.agents.llm import solar
from app.agents.state import InterviewState

logger = logging.getLogger(__name__)

_AGENTS = ["resume", "trend", "stress"]
_TREND_LIMIT = 2  # 면접당 trend 질문 최대 횟수


class RouteDecision(BaseModel):
    """meta의 다음 면접관 선택 결과 (구조화 출력)."""

    next_agent: Literal["resume", "trend", "stress"] = Field(
        description="다음에 질문할 면접관"
    )
    reason: str = Field(description="이 면접관을 고른 한 줄 이유")


_router_llm = solar.with_structured_output(RouteDecision)

SYSTEM_PROMPT = """당신은 면접 진행을 총괄하는 오케스트레이터입니다.
다음에 어떤 면접관에게 질문을 넘길지 결정하세요.

면접관 종류:
- resume: 이력서·자소서 기반 경험 검증 질문
- trend: 직무·산업 트렌드 질문
- stress: 직전 답변의 약점을 파고드는 압박·꼬리 질문

판단 기준:
- 직전 답변이 모호하거나 근거가 부족하면 stress로 꼬리질문을 이어간다
- 세 유형을 고르게 다루되, 아직 안 쓴 유형을 우선 고려한다
- trend는 면접당 1~2회면 충분하다"""


def _least_used(history: list[str], candidates: list[str]) -> str:
    """agent_history에서 가장 적게 쓰인 면접관을 고른다 (동점이면 candidates 순서 우선)."""
    return min(candidates, key=history.count)


def _record(state: InterviewState, agent: str, reason: str) -> list[dict]:
    """meta 라우팅 결정을 누적 기록한다 (발표·디버깅용)."""
    return state.get("meta_decisions", []) + [
        {"round": state["round"], "agent": agent, "reason": reason}
    ]


def _quality_gate(state: InterviewState) -> tuple[bool, str]:
    """직전 답변 품질이 낮으면 stress로 강제 라우팅한다."""
    quality = state.get("last_answer_quality") or {}
    flags = set(quality.get("flags") or [])
    score = int(quality.get("score") or 0)
    action_hint = quality.get("action_hint")

    trigger_flags = {
        "too_short",
        "evasive",
        "repetition",
        "irrelevant",
        "off_topic",
        "unsupported_claim",
        "inconsistent",
    }
    if action_hint == "stress" or score <= 45 or flags & trigger_flags:
        reason = (
            "직전 답변 품질 저하 감지"
            f"(score={score}, hint={action_hint or 'none'}, flags={','.join(sorted(flags)) or 'none'})"
        )
        return True, reason
    return False, ""


async def meta_agent(state: InterviewState) -> InterviewState:
    """
    역할: 종료 판단 + 다음 면접관(resume/trend/stress) 적응적 선택.
    - round >= max_rounds → is_done, judge로 라우팅
    - round 0 → resume로 시작 (이력서 기반 오프닝)
    - 그 외 → LLM이 직전 답변·진행 상황을 보고 선택
      (실패 시 agent_history 기반 폴백, trend는 면접당 최대 2회로 제한)
    선택 이유는 meta_decisions에 기록한다.
    """
    if state["round"] >= state["max_rounds"]:
        return {
            **state,
            "is_done": True,
            "current_agent": "judge",
            "meta_decisions": _record(state, "judge", "최대 라운드 도달 — 면접 종료"),
        }

    if state["round"] == 0 or not state["messages"]:
        return {
            **state,
            "current_agent": "resume",
            "meta_decisions": _record(state, "resume", "면접 시작 — 이력서 기반 오프닝"),
        }

    force_stress, force_reason = _quality_gate(state)
    if force_stress:
        return {
            **state,
            "current_agent": "stress",
            "meta_decisions": _record(state, "stress", force_reason),
        }

    history = state["agent_history"]
    try:
        user_prompt = (
            f"지금까지 호출된 면접관 순서: {history}\n"
            f"지원자의 직전 답변: {state.get('last_answer') or '(없음)'}\n\n"
            f"[면접 대화]\n{format_transcript(state['messages'])}\n\n"
            f"다음 면접관을 선택하세요."
        )
        decision: RouteDecision = await _router_llm.ainvoke(
            [("system", SYSTEM_PROMPT), ("human", user_prompt)]
        )
        next_agent, reason = decision.next_agent, decision.reason
    except Exception:
        logger.exception("meta 라우팅 실패 — agent_history 기반 폴백")
        next_agent = _least_used(history, _AGENTS)
        reason = "LLM 라우팅 실패 — 가장 적게 쓰인 면접관으로 폴백"

    # trend 횟수 하드 캡 — 프롬프트만으론 LLM이 계속 trend를 고를 수 있음
    if next_agent == "trend" and history.count("trend") >= _TREND_LIMIT:
        next_agent = _least_used(history, ["resume", "stress"])
        reason = f"trend {_TREND_LIMIT}회 도달 — {next_agent}(으)로 대체"

    return {
        **state,
        "current_agent": next_agent,
        "meta_decisions": _record(state, next_agent, reason),
    }


def route_to_agent(state: InterviewState) -> str:
    """conditional_edges용 라우팅 함수. state 손상 시 resume로 방어적 폴백."""
    if state["is_done"]:
        return "judge"
    return state.get("current_agent") or "resume"
