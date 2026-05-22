"""에이전트 공용 헬퍼 — 프롬프트 구성에 쓰인다."""

_QUOTE_CHARS = "\"'“”‘’"


def format_transcript(messages: list[dict]) -> str:
    """messages 목록을 '면접관/지원자' 형식의 읽기 좋은 텍스트로 변환한다."""
    if not messages:
        return "(아직 대화 없음)"
    lines = []
    for m in messages:
        speaker = "면접관" if m.get("role") == "interviewer" else "지원자"
        lines.append(f"{speaker}: {m.get('content', '')}")
    return "\n".join(lines)


def clean_question(text: str) -> str:
    """LLM이 질문을 따옴표·공백으로 감싸 출력한 경우를 정리한다."""
    return text.strip().strip(_QUOTE_CHARS).strip()
