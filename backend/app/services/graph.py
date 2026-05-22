from langgraph.graph import StateGraph, END

from app.agents.state import InterviewState
from app.agents.meta import meta_agent, route_to_agent
from app.agents.resume import resume_agent
from app.agents.trend import trend_agent
from app.agents.stress import stress_agent
from app.agents.judge import judge_agent


def build_interview_graph():
    graph = StateGraph(InterviewState)

    graph.add_node("meta", meta_agent)
    graph.add_node("resume", resume_agent)
    graph.add_node("trend", trend_agent)
    graph.add_node("stress", stress_agent)
    graph.add_node("judge", judge_agent)

    graph.set_entry_point("meta")

    graph.add_conditional_edges("meta", route_to_agent, {
        "resume": "resume",
        "trend": "trend",
        "stress": "stress",
        "judge": "judge",
    })

    graph.add_edge("resume", END)
    graph.add_edge("trend", END)
    graph.add_edge("stress", END)
    graph.add_edge("judge", END)

    return graph.compile()
