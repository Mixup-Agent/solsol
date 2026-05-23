"""에이전트 공용 LLM — Upstage Solar Pro3 (역할별 분리).

Solar Pro3의 고유 기능을 활용해 인스턴스를 3개로 분리한다:
- solar (Pro3, reasoning_effort='low'): 질문 생성기 — resume/trend/stress
- solar_reasoner (Pro3, reasoning_effort='high'): 추론 엔진 — meta/judge
- solar_classifier (solar-mini): 분류기 — answer_quality
"""
from langchain_upstage import ChatUpstage

from app.config import settings

# 질문 생성기 — resume / trend / stress
solar = ChatUpstage(
    model="solar-pro3",
    api_key=settings.upstage_api_key,
    reasoning_effort="low",
)

# 추론 엔진 — meta(라우팅) / judge(평가)
solar_reasoner = ChatUpstage(
    model="solar-pro3",
    api_key=settings.upstage_api_key,
    reasoning_effort="high",
)

# 분류기 — answer_quality(답변 품질 진단)
solar_classifier = ChatUpstage(
    model="solar-mini",
    api_key=settings.upstage_api_key,
)


def with_session_cache(llm, session_id: str):
    """세션별 prompt_cache_key를 동적으로 주입한다.

    같은 면접 세션 안에서 시스템 프롬프트·이력서·자소서가 반복 전송되므로
    세션 ID를 캐시 키로 박아 두 번째 라운드부터 캐시 히트로 비용·지연 절감.
    bind를 먼저 적용한 뒤 with_structured_output을 거는 순서를 반드시 지킨다.
    """
    if not session_id:
        return llm
    return llm.bind(extra_body={"prompt_cache_key": f"interview:{session_id}"})
