from app.agents.state import InterviewState


async def meta_agent(state: InterviewState) -> InterviewState:
    """
    역할: 다음 에이전트 결정, 난이도 조절, 종료 판단
    - round >= max_rounds 이면 is_done = True, current_agent = "judge"
    - 그 외에는 resume / trend / stress 중 하나를 current_agent에 설정
    TODO (에이전트 팀): 프롬프트 고도화, 답변 품질 기반 난이도 조절 로직
    """
    if state["round"] >= state["max_rounds"]:
        return {**state, "is_done": True, "current_agent": "judge"}

    agents = ["resume", "trend", "stress"]
    next_agent = agents[state["round"] % 3]

    return {**state, "current_agent": next_agent}


def route_to_agent(state: InterviewState) -> str:
    """conditional_edges용 라우팅 함수"""
    if state["is_done"]:
        return "judge"
    return state["current_agent"]
