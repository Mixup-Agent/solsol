import json

from app.agents.state import InterviewState
from langchain_upstage import ChatUpstage
from app.config import settings

llm = ChatUpstage(model="solar-pro", api_key=settings.upstage_api_key)


async def judge_agent(state: InterviewState) -> InterviewState:
    """
    역할: 전체 면접 평가, 점수화, 피드백 생성
    출력: scores (logic, experience, trend 각 0-100), feedback 텍스트
    TODO (에이전트 팀): 평가 기준 정교화, 개선 질문 리스트 추가
    """
    prompt = f"""
    당신은 면접 평가자입니다.
    전체 대화: {state['messages']}
    직무: {state['role']}
    회사: {state['company']}

    아래 JSON 형식으로만 응답하세요:
    {{
        "logic": 0~100,
        "experience": 0~100,
        "trend": 0~100,
        "feedback": "종합 피드백 텍스트"
    }}
    """
    response = await llm.ainvoke(prompt)
    result = json.loads(response.content)

    return {
        **state,
        "scores": {
            "logic": result["logic"],
            "experience": result["experience"],
            "trend": result["trend"],
        },
        "feedback": result["feedback"],
        "is_done": True,
    }
