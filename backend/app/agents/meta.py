"""meta 에이전트 — 다음 면접관을 적응적으로 선택하고 종료를 판단한다."""
import logging
from typing import Literal

from pydantic import BaseModel, Field

from app.agents.helpers import format_transcript
from app.agents.llm import solar
from app.agents.state import InterviewState

logger = logging.getLogger(__name__)

_AGENTS = ["resume", "trend", "stress"]


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


async def meta_agent(state: InterviewState) -> InterviewState:
    """
    역할: 종료 판단 + 다음 면접관(resume/trend/stress) 적응적 선택.
    - round >= max_rounds → is_done, judge로 라우팅
    - round 0 → resume로 시작 (이력서 기반 오프닝)
    - 그 외 → LLM이 직전 답변·진행 상황을 보고 선택 (실패 시 라운드로빈 폴백)
    """
    if state["round"] >= state["max_rounds"]:
        return {**state, "is_done": True, "current_agent": "judge"}

    if state["round"] == 0 or not state["messages"]:
        return {**state, "current_agent": "resume"}

    try:
        user_prompt = (
            f"지금까지 호출된 면접관 순서: {state['agent_history']}\n"
            f"지원자의 직전 답변: {state.get('last_answer') or '(없음)'}\n\n"
            f"[면접 대화]\n{format_transcript(state['messages'])}\n\n"
            f"다음 면접관을 선택하세요."
        )
        decision: RouteDecision = await _router_llm.ainvoke(
            [("system", SYSTEM_PROMPT), ("human", user_prompt)]
        )
        next_agent = decision.next_agent
    except Exception:
        logger.exception("meta 라우팅 실패 — 라운드로빈 폴백")
        next_agent = _AGENTS[state["round"] % 3]

    return {**state, "current_agent": next_agent}


def route_to_agent(state: InterviewState) -> str:
    """conditional_edges용 라우팅 함수."""
    if state["is_done"]:
        return "judge"
    return state["current_agent"]
