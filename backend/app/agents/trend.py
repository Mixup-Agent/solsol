from app.agents.state import InterviewState
from langchain_anthropic import ChatAnthropic
from app.config import settings

llm = ChatAnthropic(model="claude-sonnet-4-6", api_key=settings.anthropic_api_key)


async def trend_agent(state: InterviewState) -> InterviewState:
    """
    역할: 최신 기술/산업 트렌드 기반 질문 생성
    TODO (에이전트 팀): RAG 연결 (뉴스, 기술 블로그), 웹서치 도구 추가
    """
    prompt = f"""
    당신은 면접관입니다.
    직무: {state['role']}
    회사: {state['company']}
    채용공고: {state.get('job_posting_text', '')}

    최신 기술 트렌드와 관련된 질문 1개를 생성하세요.
    질문만 출력하세요.
    """
    response = await llm.ainvoke(prompt)
    question = response.content

    new_messages = state["messages"] + [{"role": "interviewer", "content": question}]

    return {
        **state,
        "current_question": question,
        "messages": new_messages,
        "agent_history": state["agent_history"] + ["trend"],
    }
