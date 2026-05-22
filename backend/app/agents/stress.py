"""stress 에이전트 — 직전 답변의 약점을 파고드는 압박 질문을 생성한다."""
from app.agents.helpers import clean_question, format_transcript
from app.agents.llm import solar
from app.agents.state import InterviewState

SYSTEM_PROMPT = """당신은 압박 면접관입니다.
지원자의 직전 답변에서 약점·모순·모호함을 찾아 논리를 검증하는 꼬리 질문 1개를 만듭니다.

규칙:
- 직전 답변을 구체적으로 겨냥한다 (일반론 금지)
- 적당히 의심하는 톤을 유지하되 무례하지 않게 한다
- 한국어로, 질문 문장 하나만 출력한다 (따옴표·번호·머리말 없이)"""


async def stress_agent(state: InterviewState) -> InterviewState:
    """압박·논리 반박·꼬리 질문 생성. TODO (에이전트 팀): 압박 강도 동적 조절."""
    last_answer = state.get("last_answer") or "(직전 답변 없음)"
    user_prompt = (
        f"[지원자의 직전 답변]\n{last_answer}\n\n"
        f"[지금까지의 면접 대화]\n{format_transcript(state['messages'])}\n\n"
        f"직전 답변의 약점을 파고드는 압박 질문 1개를 만들어 주세요."
    )
    response = await solar.ainvoke([("system", SYSTEM_PROMPT), ("human", user_prompt)])
    question = clean_question(response.content)

    return {
        **state,
        "current_question": question,
        "messages": state["messages"] + [{"role": "interviewer", "content": question}],
        "agent_history": state["agent_history"] + ["stress"],
    }
