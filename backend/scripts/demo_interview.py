"""면접 그래프 엔드투엔드 데모 — 실제 Solar 호출로 전체 흐름을 출력한다.

실행: cd backend && uv run python scripts/demo_interview.py

Redis·HTTP 없이 LangGraph(app/services/graph.py)만 직접 구동한다.
routers/interview.py의 start→answer 루프를 그대로 재현하되, 지원자 답변은
미리 준비한 샘플로 시뮬레이션한다.
"""
import asyncio
import sys
from pathlib import Path

# scripts/ 에서 직접 실행할 때 backend/ 를 import 경로에 추가
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agents.state import InterviewState  # noqa: E402
from app.services.graph import build_interview_graph  # noqa: E402

# --- 데모용 샘플 입력 ---
SAMPLE_RESUME = (
    "스타트업 A 백엔드 엔지니어 2년. 주문 처리 API 개발, "
    "모놀리식→MSA 전환 프로젝트 주도. Python/FastAPI/PostgreSQL/Docker 사용."
)
SAMPLE_COVER_LETTER = (
    "사용자가 체감하는 성능을 중요하게 생각합니다. 느린 API를 개선하는 과정에서 "
    "병목을 데이터로 찾아내고 해결하는 일에 보람을 느꼈습니다."
)
SAMPLE_COMPANY = "테크스타트업"
SAMPLE_ROLE = "백엔드 개발자"

# 라운드별 지원자 답변 (시뮬레이션)
SAMPLE_ANSWERS = [
    "MSA 전환 프로젝트를 주도해 주문 서비스의 응답 지연을 40% 줄였습니다. "
    "부하 테스트로 병목을 찾아 캐시 계층과 비동기 처리를 도입했습니다.",
    "서비스 간 데이터 일관성은 이벤트 기반 메시징과 보상 트랜잭션으로 처리했습니다.",
    "최근에는 LLM 기반 기능이 백엔드 설계에 영향을 준다고 보고, "
    "비동기 처리와 비용 모니터링을 함께 고민하고 있습니다.",
]
MAX_ROUNDS = 3  # 데모용으로 짧게 (실서비스 기본값은 8)


def _divider(title: str) -> None:
    print(f"\n{'=' * 64}\n  {title}\n{'=' * 64}")


async def main() -> None:
    graph = build_interview_graph()

    state: InterviewState = {
        "session_id": "demo-001",
        "cover_letter": SAMPLE_COVER_LETTER,
        "resume_text": SAMPLE_RESUME,
        "portfolio_text": None,
        "company": SAMPLE_COMPANY,
        "role": SAMPLE_ROLE,
        "job_posting_text": None,
        "round": 0,
        "max_rounds": MAX_ROUNDS,
        "messages": [],
        "agent_history": [],
        "current_agent": None,
        "current_question": None,
        "last_answer": None,
        "is_done": False,
        "scores": {},
        "feedback": None,
        "meta_decisions": [],
    }

    _divider(f"면접 시작 — {SAMPLE_COMPANY} / {SAMPLE_ROLE}")
    state = await graph.ainvoke(state)
    print(f"[R{state['round']}] 🧑‍💼 면접관({state['current_agent']}):")
    print(f"     {state['current_question']}")

    # routers/interview.py의 answer 루프 재현
    for answer in SAMPLE_ANSWERS:
        state["messages"].append({"role": "candidate", "content": answer})
        state["last_answer"] = answer
        state["round"] += 1
        print(f"\n     🙋 지원자: {answer}")

        state = await graph.ainvoke(state)

        if state["is_done"]:
            break
        print(f"\n[R{state['round']}] 🧑‍💼 면접관({state['current_agent']}):")
        print(f"     {state['current_question']}")

    _divider("면접 종료 — judge 평가 리포트")
    s = state["scores"]
    print(f"종합 {s.get('overall')}/100   "
          f"논리 {s.get('logic')}  경험 {s.get('experience')}  트렌드 {s.get('trend')}")
    print(f"\n[피드백]\n{state['feedback']}")
    print(f"\n에이전트 호출 순서: {' → '.join(state['agent_history'])} → judge")
    print("\n[meta 라우팅 결정 — 왜 그 면접관을 골랐나]")
    for d in state.get("meta_decisions", []):
        print(f"  R{d['round']} → {d['agent']}: {d['reason']}")


if __name__ == "__main__":
    asyncio.run(main())
