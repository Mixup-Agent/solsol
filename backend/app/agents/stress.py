"""stress 에이전트 — 직전 답변의 약점을 파고드는 압박 질문을 생성한다."""
import re

from pydantic import BaseModel, Field

from app.agents.helpers import clean_question, format_transcript
from app.agents.llm import solar, with_session_cache
from app.agents.state import InterviewState

SYSTEM_PROMPT = """당신은 압박 면접관입니다.
지원자의 직전 답변에서 약점·모순·모호함을 찾아 논리를 검증하는 꼬리 질문 1개를 만듭니다.

규칙:
- 반드시 직전 답변의 핵심 표현 1개를 인용해 그 지점을 검증한다
- 직전 질문/답변 범위를 벗어난 새 주제를 꺼내지 않는다
- 적당히 의심하는 톤을 유지하되 무례하지 않게 한다
- 한국어로, 질문 문장 하나만 출력한다 (따옴표·번호·머리말 없이)"""


class StressQuestion(BaseModel):
    """stress 질문 구조화 출력."""

    weakness_point: str = Field(description="직전 답변에서 검증이 필요한 핵심 약점")
    follow_up_question: str = Field(description="약점을 검증하는 꼬리 질문 1문장")


_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9가-힣]{2,}")


def _last_interviewer_question(messages: list[dict]) -> str:
    for message in reversed(messages):
        if message.get("role") == "interviewer":
            return message.get("content", "")
    return ""


def _token_set(text: str) -> set[str]:
    return {token.lower() for token in _TOKEN_PATTERN.findall(text or "")}


def _is_contextual_question(question: str, last_question: str, last_answer: str) -> bool:
    scope_tokens = _token_set(last_question) | _token_set(last_answer)
    if not scope_tokens:
        return True
    question_tokens = _token_set(question)
    # 완전히 동떨어진 질문을 막기 위한 최소 중첩 기준
    return len(scope_tokens & question_tokens) >= 1


def _fallback_question(last_answer: str, last_question: str) -> str:
    anchor = (last_answer or last_question or "방금 답변").strip()
    anchor = anchor[:28].rstrip()
    return (
        f"방금 답변에서 '{anchor}'라고 말씀하셨는데, "
        "이를 뒷받침하는 수치나 실제 사례를 하나만 구체적으로 설명해 주시겠어요?"
    )


async def stress_agent(state: InterviewState) -> InterviewState:
    """압박·논리 반박·꼬리 질문 생성. TODO (에이전트 팀): 압박 강도 동적 조절."""
    last_answer = state.get("last_answer") or "(직전 답변 없음)"
    last_question = _last_interviewer_question(state.get("messages", []))
    quality = state.get("last_answer_quality") or {}
    quality_brief = (
        f"score={quality.get('score', 'n/a')}, "
        f"flags={','.join(quality.get('flags', [])) or 'none'}, "
        f"feedback={quality.get('feedback', '')}"
    )
    user_prompt = (
        f"[직전 면접관 질문]\n{last_question or '(없음)'}\n\n"
        f"[지원자의 직전 답변]\n{last_answer}\n\n"
        f"[답변 품질 진단]\n{quality_brief}\n\n"
        f"[최근 면접 대화]\n{format_transcript(state['messages'][-6:])}\n\n"
        f"직전 답변의 약점을 파고드는 압박 질문 1개를 만들어 주세요."
    )
    try:
        llm = with_session_cache(solar, state["session_id"])
        structured_llm = llm.with_structured_output(StressQuestion)
        result: StressQuestion = await structured_llm.ainvoke(
            [("system", SYSTEM_PROMPT), ("human", user_prompt)]
        )
        question = clean_question(result.follow_up_question)
    except Exception:
        question = _fallback_question(last_answer=last_answer, last_question=last_question)

    if not _is_contextual_question(question, last_question=last_question, last_answer=last_answer):
        question = _fallback_question(last_answer=last_answer, last_question=last_question)

    return {
        **state,
        "current_question": question,
        "current_question_sources": [],
        "messages": state["messages"] + [{"role": "interviewer", "content": question}],
        "agent_history": state["agent_history"] + ["stress"],
    }
