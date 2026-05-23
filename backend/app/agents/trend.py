"""trend 에이전트 — 직무·산업 트렌드 기반 질문을 생성한다."""
from app.agents.helpers import clean_question
from app.agents.llm import solar, with_session_cache
from app.agents.state import InterviewState
from app.services.naver_news import build_trend_news_context, load_trend_news_sources

SYSTEM_PROMPT = """당신은 산업·기술 트렌드를 묻는 면접관입니다.
지원자의 직무와 관련된 최신 트렌드·이슈에 대한 견해를 묻는 질문 1개를 만듭니다.

규칙:
- 직무와 동떨어진 일반 상식 질문은 피한다
- 단순 지식 확인이 아니라 의견·적용 방안을 묻는다
- 한국어로, 질문 문장 하나만 출력한다 (따옴표·번호·머리말 없이)"""


async def trend_agent(state: InterviewState) -> InterviewState:
    """최신 기술·산업 트렌드 기반 질문 생성. Naver 뉴스 DB 컨텍스트를 함께 사용."""
    job_posting = state.get("job_posting_text") or "(채용공고 정보 없음)"
    news_sources = load_trend_news_sources(
        role=state["role"],
        company=state["company"],
        job_posting_text=job_posting,
        limit=3,
    )
    news_context = build_trend_news_context(
        role=state["role"],
        company=state["company"],
        job_posting_text=job_posting,
        limit=5,
    )
    news_block = news_context or "(연결된 네이버 뉴스 데이터 없음)"
    style = state.get("company_style") or {}
    style_hint = (
        f"[회사 면접 스타일 가이드]\n"
        f"- 회사: {state['company']}\n"
        f"- 격식: {style.get('formality', 'neutral')}\n"
        f"- 중점 평가: {', '.join(style.get('focus_areas', [])) or '미정'}\n"
        f"- 질문 톤: {style.get('question_style', '구체적 경험 기반')}\n"
        f"- 알려진 면접 관행: {', '.join(style.get('known_interview_practices', [])) or '없음'}\n"
        f"위 스타일에 맞는 질문을 생성하세요.\n\n"
    )
    user_prompt = style_hint + (
        f"직무: {state['role']}\n"
        f"회사: {state['company']}\n"
        f"[채용공고 발췌]\n{job_posting}\n\n"
        f"{news_block}\n\n"
        f"이 직무와 관련된 최신 트렌드 질문 1개를 만들어 주세요."
    )
    llm = with_session_cache(solar, state["session_id"])
    response = await llm.ainvoke([("system", SYSTEM_PROMPT), ("human", user_prompt)])
    question = clean_question(response.content)

    return {
        **state,
        "current_question": question,
        "current_question_sources": news_sources,
        "messages": state["messages"] + [{"role": "interviewer", "content": question}],
        "agent_history": state["agent_history"] + ["trend"],
    }
