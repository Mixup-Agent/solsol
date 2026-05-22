from app.agents.state import InterviewState
from langchain_upstage import ChatUpstage
from app.config import settings

llm = ChatUpstage(model="solar-pro", api_key=settings.upstage_api_key)


async def stress_agent(state: InterviewState) -> InterviewState:
    """
    역할: 압박 질문, 논리 반박, 꼬리 질문
    스타일: 의심형, 비협조적
    TODO (에이전트 팀): 압박 강도 조절 로직, 이전 답변 기반 꼬리 질문
    """
    last_answer = state.get("last_answer", "")
    prompt = f"""
    당신은 압박 면접관입니다.
    지원자의 마지막 답변: {last_answer}
    대화 히스토리: {state['messages']}

    지원자의 논리를 흔드는 압박 질문 1개를 생성하세요.
    질문만 출력하세요.
    """
    response = await llm.ainvoke(prompt)
    question = response.content

    new_messages = state["messages"] + [{"role": "interviewer", "content": question}]

    return {
        **state,
        "current_question": question,
        "messages": new_messages,
        "agent_history": state["agent_history"] + ["stress"],
    }
