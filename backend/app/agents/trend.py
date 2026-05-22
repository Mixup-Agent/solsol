"""trend 에이전트 — 직무·산업 트렌드 기반 질문을 생성한다."""
from app.agents.helpers import clean_question
from app.agents.llm import solar
from app.agents.state import InterviewState

SYSTEM_PROMPT = """당신은 산업·기술 트렌드를 묻는 면접관입니다.
지원자의 직무와 관련된 최신 트렌드·이슈에 대한 견해를 묻는 질문 1개를 만듭니다.

규칙:
- 직무와 동떨어진 일반 상식 질문은 피한다
- 단순 지식 확인이 아니라 의견·적용 방안을 묻는다
- 한국어로, 질문 문장 하나만 출력한다 (따옴표·번호·머리말 없이)"""


async def trend_agent(state: InterviewState) -> InterviewState:
    """최신 기술·산업 트렌드 기반 질문 생성. TODO (에이전트 팀): 웹서치/RAG 연동."""
    job_posting = state.get("job_posting_text") or "(채용공고 정보 없음)"
    user_prompt = (
        f"직무: {state['role']}\n"
        f"회사: {state['company']}\n"
        f"[채용공고 발췌]\n{job_posting}\n\n"
        f"이 직무와 관련된 최신 트렌드 질문 1개를 만들어 주세요."
    )
    response = await solar.ainvoke([("system", SYSTEM_PROMPT), ("human", user_prompt)])
    question = clean_question(response.content)

    return {
        **state,
        "current_question": question,
        "messages": state["messages"] + [{"role": "interviewer", "content": question}],
        "agent_history": state["agent_history"] + ["trend"],
    }
