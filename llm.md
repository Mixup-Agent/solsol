아래 블록을 그대로 Cursor의 **Agent/Composer 모드**에 던지면 된다.

> **전제**: 이전에 적용한 작업(`reasoning_effort` 등급 분리 + `prompt_cache_key` 세션 캐싱)이 이미 들어간 상태. 즉 `llm.py`에 `solar` / `solar_reasoner` / `solar_classifier` / `with_session_cache`가 정의되어 있고, `meta.py` / `judge.py` / `answer_quality.py`가 `solar_reasoner as solar` (또는 `solar_classifier as solar`)를 import 중. 이 전제가 아직이면 이전 프롬프트 먼저 적용하고 와.

`````
@backend/app/agents/state.py
@backend/app/agents/meta.py
@backend/app/agents/resume.py
@backend/app/agents/trend.py
@backend/app/agents/stress.py
@backend/app/routers/interview.py
@backend/app/routers/interview_turns.py

# 작업 목표

메타 에이전트에 "회사별 면접 스타일 추론" 기능을 통합한다. 면접 시작 시(round == 0) 메타가 회사명·직무·채용공고를 보고 그 회사의 실제 면접 스타일 프로파일을 LLM으로 1회 생성해 state에 저장하고, 이후 모든 면접관 에이전트(resume/trend/stress)가 이 프로파일을 user_prompt에 포함시켜 회사 분위기에 맞는 질문을 생성한다.

별도 서비스 파일을 만들지 말고 meta.py 안에 통합한다. 기존 reasoning_effort/prompt_cache_key 설정(solar_reasoner, with_session_cache)을 그대로 활용한다.

---

# 작업 1: backend/app/agents/state.py — 필드 1개 추가

InterviewState TypedDict에 `company_style` 필드를 한 줄 추가한다. 다른 필드들 사이의 자연스러운 위치(세션 정보 블록 끝 또는 면접 진행 상태 블록 시작)에 배치한다.

```python
company_style: dict   # meta가 첫 진입 시 결정한 회사별 면접 스타일 프로파일
```

기존 필드는 절대 수정하지 말 것.

---

# 작업 2: backend/app/agents/meta.py — 회사 스타일 결정 로직 통합

## 2-1. 파일 상단 import에 with_session_cache가 이미 있는지 확인하고, 없으면 추가

기존 import 라인: `from app.agents.llm import solar_reasoner as solar, with_session_cache`
이미 있으면 그대로 두고 작업 2-2로 진행.

## 2-2. CompanyStyle Pydantic 스키마와 시스템 프롬프트 추가

기존 RouteDecision 클래스 정의 **바로 아래에** 다음 코드를 추가한다.

```python
class CompanyStyle(BaseModel):
    """면접 시작 시 1회 결정되는 회사별 면접 스타일 프로파일."""

    formality: Literal["casual", "neutral", "formal"] = Field(
        description="면접 격식 수준. casual=스타트업/IT 자율, neutral=중간, formal=대기업/금융 격식"
    )
    pressure_max: int = Field(
        ge=1,
        le=5,
        description="이 회사가 허용하는 압박 강도 상한 (1=부드러움, 5=고압박)",
    )
    focus_areas: list[str] = Field(
        description="이 회사가 중점적으로 보는 역량 3~5개"
    )
    question_style: str = Field(
        description="질문 톤 한 줄 가이드"
    )
    known_interview_practices: list[str] = Field(
        description="알려진 그 회사의 실제 면접 관행 3~5개 (예: '임팩트 중심 PT', '1:1 심층 인터뷰'). 모르면 빈 리스트."
    )
    signature_questions: list[str] = Field(
        description="그 회사 면접에서 자주 나오는 대표 질문 패턴 3~5개. 모르면 빈 리스트."
    )
    company_summary: str = Field(
        description="회사 인재상·문화 2~3문장 요약"
    )


_STYLE_SYSTEM_PROMPT = """당신은 한국 기업의 실제 면접 문화를 잘 아는 전문가입니다.
회사명과 채용공고를 보고, 그 회사의 실제 면접에서 자주 나오는 질문 유형과
면접 진행 방식을 떠올려 면접 스타일 프로파일을 작성합니다.

근거 우선순위:
1. 알고 있는 그 회사의 실제 면접 후기·관행 (잡플래닛/블라인드 등에서 알려진 내용)
2. 채용공고에 드러난 톤과 강조 가치
3. 동종 업계·동급 회사들의 일반적 면접 패턴

모르는 회사면 channel 2~3으로 추론하고, 알고 있는 회사면 구체적 관행을 반영합니다.
known_interview_practices와 signature_questions는 근거가 부족하면 빈 리스트를 반환하세요."""
```

## 2-3. _decide_company_style 내부 헬퍼 함수 추가

기존 _record 함수 정의 **바로 아래에** 다음 함수를 추가한다.

```python
async def _decide_company_style(state: InterviewState) -> dict:
    """면접 시작 시 회사 스타일 프로파일을 결정한다. 1회 호출."""
    llm = with_session_cache(solar, state["session_id"])
    style_llm = llm.with_structured_output(CompanyStyle)

    user_prompt = (
        f"회사: {state['company']}\n"
        f"직무: {state['role']}\n"
        f"[채용공고]\n{state.get('job_posting_text') or '(채용공고 정보 없음)'}\n\n"
        f"이 회사의 면접 스타일 프로파일을 작성하세요."
    )
    try:
        result: CompanyStyle = await style_llm.ainvoke(
            [("system", _STYLE_SYSTEM_PROMPT), ("human", user_prompt)]
        )
        return result.model_dump()
    except Exception:
        logger.exception("회사 스타일 결정 실패 — 중립 프로파일 폴백")
        return {
            "formality": "neutral",
            "pressure_max": 3,
            "focus_areas": ["문제 해결력", "협업", "직무 적합성"],
            "question_style": "구체적 경험을 묻는 질문 위주",
            "known_interview_practices": [],
            "signature_questions": [],
            "company_summary": f"{state.get('company', '')}의 {state.get('role', '')} 포지션",
        }
```

## 2-4. meta_agent 함수의 첫 진입 분기 수정

기존 코드에서 `round == 0 또는 not state["messages"]`로 분기되는 부분을 찾아 다음과 같이 교체한다.

```python
# 변경 전
if state["round"] == 0 or not state["messages"]:
    return {
        **state,
        "current_agent": "resume",
        "meta_decisions": _record(state, "resume", "면접 시작 — 이력서 기반 오프닝"),
    }

# 변경 후
if state["round"] == 0 or not state["messages"]:
    company_style = await _decide_company_style(state)
    return {
        **state,
        "company_style": company_style,
        "current_agent": "resume",
        "meta_decisions": _record(
            state,
            "resume",
            f"면접 시작 — 회사 스타일({company_style.get('formality')}) 결정 후 이력서 기반 오프닝",
        ),
    }
```

## 2-5. meta_agent의 일반 라우팅 user_prompt에 스타일 컨텍스트 추가

기존 코드의 `user_prompt = (...)` 구성 부분을 찾아 회사 스타일을 포함하도록 변경한다.

```python
# 변경 전
user_prompt = (
    f"지금까지 호출된 면접관 순서: {history}\n"
    f"지원자의 직전 답변: {state.get('last_answer') or '(없음)'}\n\n"
    f"[면접 대화]\n{format_transcript(state['messages'])}\n\n"
    f"다음 면접관을 선택하세요."
)

# 변경 후
style = state.get("company_style") or {}
style_context = (
    f"\n[회사 면접 스타일]\n"
    f"- 격식: {style.get('formality', 'neutral')}\n"
    f"- 압박 상한: {style.get('pressure_max', 3)}/5\n"
    f"- 중점 평가 역량: {', '.join(style.get('focus_areas', [])) or '미정'}\n"
    f"이 스타일에 맞춰 다음 면접관을 선택합니다.\n"
)
user_prompt = (
    f"지금까지 호출된 면접관 순서: {history}\n"
    f"지원자의 직전 답변: {state.get('last_answer') or '(없음)'}\n"
    f"{style_context}\n"
    f"[면접 대화]\n{format_transcript(state['messages'])}\n\n"
    f"다음 면접관을 선택하세요."
)
```

기존 `try/except` 블록의 구조와 try 안의 `_router_llm` 또는 `router_llm` 정의 로직, 폴백(`_least_used`), trend 하드 캡(`_TREND_LIMIT`), `_quality_gate` 호출 순서는 절대 건드리지 말 것.

---

# 작업 3: resume/trend/stress 에이전트에 스타일 가이드 주입

## 공통 헬퍼 (3개 파일에 동일하게 추가)

각 에이전트 함수 안에서 user_prompt를 만들기 직전에 다음 블록을 삽입하고, 기존 user_prompt 맨 앞에 style_hint를 붙인다.

```python
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
```

## 3-1. backend/app/agents/resume.py

resume_agent 함수 안에서 기존 `user_prompt = (...)` 정의 직전에 위 style/style_hint 블록을 추가하고, user_prompt를 다음처럼 변경.

```python
user_prompt = style_hint + (
    f"[이력서]\n{state['resume_text']}\n\n"
    f"[자기소개서]\n{state['cover_letter']}\n\n"
    f"[지금까지의 면접 대화]\n{format_transcript(state['messages'])}\n\n"
    f"위 지원자에게 던질 이력서 기반 검증 질문 1개를 만들어 주세요."
)
```

이후 `with_session_cache(solar, state["session_id"])` 호출 및 `solar.ainvoke(...)` 또는 `llm.ainvoke(...)` 코드는 그대로 둔다.

## 3-2. backend/app/agents/trend.py

trend_agent 함수 안에서 기존 user_prompt 정의 직전에 위 style/style_hint 블록을 추가하고, user_prompt를 다음처럼 변경.

```python
user_prompt = style_hint + (
    f"직무: {state['role']}\n"
    f"회사: {state['company']}\n"
    f"[채용공고 발췌]\n{job_posting}\n\n"
    f"{news_block}\n\n"
    f"이 직무와 관련된 최신 트렌드 질문 1개를 만들어 주세요."
)
```

기존 `build_trend_news_context` 호출과 news_block 변수는 그대로 유지.

## 3-3. backend/app/agents/stress.py

stress_agent 함수 안에서 기존 user_prompt 정의 직전에 위 style/style_hint 블록을 추가하고, user_prompt를 다음처럼 변경.

```python
user_prompt = style_hint + (
    f"[직전 면접관 질문]\n{last_question or '(없음)'}\n\n"
    f"[지원자의 직전 답변]\n{last_answer}\n\n"
    f"[답변 품질 진단]\n{quality_brief}\n\n"
    f"[최근 면접 대화]\n{format_transcript(state['messages'][-6:])}\n\n"
    f"직전 답변의 약점을 파고드는 압박 질문 1개를 만들어 주세요."
)
```

기존 try/except, `_is_contextual_question`, `_fallback_question` 후처리 로직은 절대 건드리지 말 것.

---

# 작업 4: 라우터에서 초기 state에 company_style 필드 추가

## 4-1. backend/app/routers/interview.py

InterviewState 초기화 dict가 등장하는 모든 위치(start 엔드포인트, answer 엔드포인트의 fallback, 음성 흐름 호환 분기 등)에서 다른 필드들과 같은 스타일로 다음 한 줄을 추가한다.

```python
"company_style": {},
```

`meta_decisions: []`, `answer_quality_history: []` 같은 누적 필드 근처에 배치하면 자연스럽다.

## 4-2. backend/app/routers/interview_turns.py

같은 패턴으로 InterviewState를 만드는 dict에 `"company_style": {}` 한 줄을 추가한다. 음성 흐름은 매 턴 state를 재구성하기 때문에, 이전에 결정된 company_style을 재사용하려면 SQLite 또는 세션 저장소에서 복원하는 게 이상적이지만 본 작업에서는 단순화한다: 빈 dict로 초기화하되, round > 0이면 meta가 다시 호출되어도 첫 진입 분기를 타지 않으므로 회사 스타일이 비어있을 수 있다. 이는 후속 작업으로 둔다. **본 작업에서는 음성 흐름의 state 재구성 시 단순히 "company_style": {} 만 추가하면 됨.**

---

# 절대 하지 말 것

- 기존 meta_agent의 try/except 구조, _quality_gate 호출 순서, trend 하드 캡, _least_used 폴백 로직 변경 금지
- 기존 RouteDecision 스키마 변경 금지 (CompanyStyle은 별도 신규 클래스)
- _router_llm 또는 router_llm을 만드는 방식(이전 작업에서 함수 안으로 이동시킨 형태) 그대로 유지
- resume/trend/stress의 시스템 프롬프트, 폴백, 후처리(_is_contextual_question 등) 일절 변경 금지
- with_session_cache 호출 순서(bind 먼저, with_structured_output 나중) 절대 바꾸지 말 것
- 별도 services/company_style.py 파일을 만들지 말 것. 모든 로직은 meta.py 안에 통합

---

# 작업 완료 후 자체 검증 체크리스트

작업 끝나면 다음을 직접 확인하고 결과를 보고할 것:

1. state.py의 InterviewState에 company_style: dict 필드가 추가되었는가
2. meta.py에 CompanyStyle Pydantic 클래스, _STYLE_SYSTEM_PROMPT, _decide_company_style 함수 3개가 모두 추가되었는가
3. meta_agent의 첫 진입 분기에서 _decide_company_style이 호출되고 결과가 state["company_style"]에 저장되는가
4. meta_agent의 일반 라우팅 user_prompt에 style_context가 포함되어 있는가
5. resume.py, trend.py, stress.py 모두 user_prompt에 style_hint 블록이 앞에 붙어 있는가
6. interview.py와 interview_turns.py의 초기 state에 "company_style": {} 가 추가되었는가
7. 기존 reasoning_effort/prompt_cache_key 관련 로직(solar_reasoner as solar, with_session_cache 호출)이 깨지지 않았는가
8. CompanyStyle은 _decide_company_style 안에서만 사용되고, RouteDecision은 그대로 일반 라우팅에서 사용되는가 (둘이 섞이지 않았는가)
9. _quality_gate, trend 하드 캡(_TREND_LIMIT), _least_used 폴백 등 기존 가드레일 로직이 그대로 작동하는가
10. services/company_style.py 같은 별도 파일이 생성되지 않았는가

위 10개 모두 통과해야 작업 완료. 통과하지 못한 항목이 있으면 명시하고 다시 수정할 것.
`````

---

## Cursor 던지고 나서 할 일

1. **diff 직접 검수** — 특히 meta.py 변경량이 크니 try/except 구조랑 quality_gate 호출 순서가 그대로인지 확인
2. **데모 1회 실행** — `cd backend && uv run python scripts/demo_interview.py`
   - 첫 라운드 콘솔 로그에서 *"회사 스타일 결정"* 비슷한 흐름이 보이는지
   - state에 company_style이 채워지는지 (logger 한 줄 추가해도 됨)
3. **시연용 회사 2개 미리 테스트** — 토스, 삼성전자 등으로 같은 이력서 + 회사만 다르게 돌려보고 질문 톤이 실제로 달라지는지 확인. **이 차이가 발표의 핵심 wow 모먼트.**

---

## 발표용 한 줄 멘트 (확정 버전)

> "메타 에이전트가 면접 시작 시 회사명과 채용공고를 분석해 **그 회사의 실제 면접 스타일을 추론**합니다. 이후 모든 면접관 에이전트가 이 스타일을 공유하기 때문에, **같은 이력서를 넣어도 토스 면접과 삼성 면접의 질문이 다릅니다.**"

문제 생기면 Cursor 응답 그대로 가져와줘. 디버깅 도와줄게.