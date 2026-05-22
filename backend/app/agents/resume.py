"""resume 에이전트 — 이력서·자소서 기반 사실 검증 질문을 생성한다."""
from app.agents.helpers import clean_question, format_transcript
from app.agents.llm import solar, with_session_cache
from app.agents.state import InterviewState

SYSTEM_PROMPT = """당신은 이력서·자기소개서를 검증하는 면접관입니다.
지원자의 경험에서 구체성이 필요한 부분을 골라 사실 검증 질문 1개를 만듭니다.

규칙:
- 모호한 표현("주도했다", "개선했다")은 수치·사례·의사결정 과정을 파고든다
- 이미 나온 질문과 겹치지 않게 한다
- 한국어로, 질문 문장 하나만 출력한다 (따옴표·번호·머리말 없이)"""


async def resume_agent(state: InterviewState) -> InterviewState:
    """이력서/자소서 기반 질문 생성. 사용 데이터: resume_text, cover_letter, messages."""
    user_prompt = (
        f"[이력서]\n{state['resume_text']}\n\n"
        f"[자기소개서]\n{state['cover_letter']}\n\n"
        f"[지금까지의 면접 대화]\n{format_transcript(state['messages'])}\n\n"
        f"위 지원자에게 던질 이력서 기반 검증 질문 1개를 만들어 주세요."
    )
    llm = with_session_cache(solar, state["session_id"])
    response = await llm.ainvoke([("system", SYSTEM_PROMPT), ("human", user_prompt)])
    question = clean_question(response.content)

    return {
        **state,
        "current_question": question,
        "current_question_sources": [],
        "messages": state["messages"] + [{"role": "interviewer", "content": question}],
        "agent_history": state["agent_history"] + ["resume"],
    }
