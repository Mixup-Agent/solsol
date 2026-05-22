from typing import TypedDict, Optional


class InterviewState(TypedDict):
    # 세션 정보 (읽기 전용)
    session_id: str
    cover_letter: str
    resume_text: str
    portfolio_text: Optional[str]
    company: str
    role: str
    job_posting_text: Optional[str]

    # 면접 진행 상태
    round: int                        # 현재 라운드 (0부터 시작)
    max_rounds: int                   # 최대 라운드 수 (기본 8)
    messages: list[dict]              # 대화 히스토리 {"role": "interviewer"|"candidate", "content": "..."}
    agent_history: list[str]          # 호출된 에이전트 순서 ["resume", "trend", ...]
    meta_decisions: list[dict]        # meta 라우팅 기록 [{"round","agent","reason"}, ...]

    # 현재 턴 데이터
    current_agent: Optional[str]      # "resume" | "trend" | "stress" | "judge"
    current_question: Optional[str]   # 현재 질문 텍스트
    last_answer: Optional[str]        # 지원자의 마지막 답변

    # 종료 및 평가
    is_done: bool                     # 면접 종료 여부
    scores: dict                      # {"overall": 0, "logic": 0, "experience": 0, "trend": 0}
    feedback: Optional[str]           # 최종 피드백 텍스트
