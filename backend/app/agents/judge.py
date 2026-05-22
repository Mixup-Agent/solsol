"""judge 에이전트 — 면접 종료 시 전체 대화를 평가해 최종 리포트 데이터를 생성한다."""
import logging

from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field

from app.agents.state import InterviewState
from app.config import settings

logger = logging.getLogger(__name__)

llm = ChatAnthropic(model="claude-sonnet-4-6", api_key=settings.anthropic_api_key)


class JudgeResult(BaseModel):
    """judge 에이전트의 구조화 출력 스키마."""

    overall: int = Field(ge=0, le=100, description="종합 점수 (0-100)")
    logic: int = Field(ge=0, le=100, description="논리 점수 (0-100)")
    experience: int = Field(ge=0, le=100, description="경험 점수 (0-100)")
    trend: int = Field(ge=0, le=100, description="트렌드 점수 (0-100)")
    feedback: str = Field(description="지원자에게 전하는 3~5문장 종합 피드백")


# 구조화 출력 — Claude가 JudgeResult 스키마를 강제로 따르므로 수동 JSON 파싱 불필요
structured_llm = llm.with_structured_output(JudgeResult)

SYSTEM_PROMPT = """당신은 면접 평가 전문가입니다. 면접 전체 대화를 읽고 지원자를 평가하세요.

세 축을 각각 0-100점으로 채점합니다:
- 논리(logic): 답변의 논리적 일관성, 근거 제시, 압박 질문 대응력
- 경험(experience): 이력서·경험 기반 답변의 구체성, 사실성, 깊이
- 트렌드(trend): 직무·산업 트렌드에 대한 이해와 통찰

종합(overall)은 세 축을 고려한 전체 인상 점수입니다 (단순 평균이 아니어도 됩니다).
feedback은 지원자에게 직접 전하는 3~5문장 종합 피드백으로, 강점과 개선점을
구체적으로 균형 있게 한국어로 작성합니다."""


def _format_transcript(messages: list[dict]) -> str:
    """대화 메시지 목록을 '면접관/지원자' 형식 텍스트로 변환한다."""
    if not messages:
        return "(대화 없음)"
    lines = []
    for m in messages:
        speaker = "면접관" if m.get("role") == "interviewer" else "지원자"
        lines.append(f"{speaker}: {m.get('content', '')}")
    return "\n".join(lines)


async def judge_agent(state: InterviewState) -> InterviewState:
    """
    역할: 전체 면접을 평가해 최종 리포트 데이터를 생성한다 (질문은 하지 않음).
    출력: scores = {overall, logic, experience, trend} (각 0-100), feedback 텍스트.
    LLM 호출이나 스키마 검증이 실패하면 0점 폴백으로 리포트 엔드포인트가 죽지 않게 한다.
    """
    user_prompt = (
        f"직무: {state['role']}\n"
        f"회사: {state['company']}\n\n"
        f"=== 면접 대화 ===\n{_format_transcript(state['messages'])}\n\n"
        f"위 면접을 평가해 주세요."
    )

    try:
        result: JudgeResult = await structured_llm.ainvoke(
            [("system", SYSTEM_PROMPT), ("human", user_prompt)]
        )
        scores = {
            "overall": result.overall,
            "logic": result.logic,
            "experience": result.experience,
            "trend": result.trend,
        }
        feedback = result.feedback
    except Exception as e:
        logger.exception("judge_agent 평가 실패")
        scores = {"overall": 0, "logic": 0, "experience": 0, "trend": 0}
        feedback = f"평가 생성에 실패했습니다: {e}"

    return {
        **state,
        "scores": scores,
        "feedback": feedback,
        "is_done": True,
    }
