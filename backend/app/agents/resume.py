from app.agents.llm import solar
from app.agents.state import InterviewState


async def resume_agent(state: InterviewState) -> InterviewState:
    """
    역할: 이력서/자소서 기반 질문 생성
    데이터: cover_letter, resume_text, portfolio_text
    스타일: 사실 검증, 구체성 파고들기
    TODO (에이전트 팀): 프롬프트 작성
    """
    prompt = f"""
    당신은 면접관입니다.
    이력서: {state['resume_text']}
    자소서: {state['cover_letter']}
    대화 히스토리: {state['messages']}

    지원자의 경험을 검증하는 질문 1개를 생성하세요.
    질문만 출력하세요.
    """
    response = await solar.ainvoke(prompt)
    question = response.content

    new_messages = state["messages"] + [{"role": "interviewer", "content": question}]

    return {
        **state,
        "current_question": question,
        "messages": new_messages,
        "agent_history": state["agent_history"] + ["resume"],
    }
