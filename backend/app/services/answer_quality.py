"""답변 품질을 LLM 기반으로 진단한다."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.agents.llm import solar_classifier as solar, with_session_cache


class AnswerQualityResult(BaseModel):
    """LLM 기반 답변 품질 진단 구조화 결과."""

    score: int = Field(ge=0, le=100, description="답변 품질 점수")
    label: Literal["good", "fair", "bad"] = Field(description="답변 품질 등급")
    flags: list[
        Literal[
            "too_short",
            "evasive",
            "repetition",
            "irrelevant",
            "off_topic",
            "unsupported_claim",
            "inconsistent",
        ]
    ] = Field(default_factory=list, description="품질 저하 원인 태그")
    feedback: str = Field(description="다음 질문 설계를 위한 한 줄 피드백")
    action_hint: Literal["normal", "followup", "stress"] = Field(
        description="다음 라우팅 힌트"
    )


SYSTEM_PROMPT = """당신은 면접 답변 품질 평가기입니다.
질문, 답변, 직전 답변 이력을 보고 답변 품질을 판단하세요.

판단 기준:
- 질문과의 관련성(무관/주제이탈 여부)
- 구체성(근거/사례/수치 유무)
- 회피성("모르겠다", "답변 어렵다" 등)
- 반복/모순 여부
- 근거 없는 과장 주장 가능성

출력 규칙:
- score: 0~100
- label: good/fair/bad
- flags: 해당되는 태그만 포함
- feedback: 한국어 1문장
- action_hint:
  - normal: 다음 주제로 진행 가능
  - followup: 같은 주제에서 구체화 질문 필요
  - stress: 검증/압박 질문 필요
"""


async def evaluate_answer_quality(
    question_text: str,
    answer_text: str,
    recent_answers: list[str] | None = None,
    session_id: str = "",
) -> dict:
    """질문/답변 품질을 LLM으로 진단한다."""
    recent_answers = recent_answers or []
    user_prompt = (
        f"[질문]\n{question_text or '(없음)'}\n\n"
        f"[현재 답변]\n{answer_text or '(없음)'}\n\n"
        f"[직전 답변 이력]\n"
        + ("\n".join(f"- {a}" for a in recent_answers[-3:]) if recent_answers else "(없음)")
    )

    try:
        llm = with_session_cache(solar, session_id)
        quality_llm = llm.with_structured_output(AnswerQualityResult)
        result: AnswerQualityResult = await quality_llm.ainvoke(
            [("system", SYSTEM_PROMPT), ("human", user_prompt)]
        )
        return result.model_dump()
    except Exception:
        # LLM 실패 시 면접 흐름을 깨지 않도록 중립값으로 폴백
        return {
            "score": 55,
            "label": "fair",
            "flags": [],
            "feedback": "답변 품질 판별이 불안정하여 후속 확인 질문을 권장합니다.",
            "action_hint": "followup",
        }
