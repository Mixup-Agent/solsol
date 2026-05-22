아래 블록을 그대로 복사해서 Cursor의 **Agent/Composer 모드**에 한 번에 던지면 된다. 파일 첨부(`@`)도 포함되어 있다.

`````
@backend/app/agents/llm.py
@backend/app/agents/meta.py
@backend/app/agents/judge.py
@backend/app/agents/resume.py
@backend/app/agents/trend.py
@backend/app/agents/stress.py
@backend/app/services/answer_quality.py
@backend/app/routers/interview.py
@backend/app/routers/interview_turns.py

# 작업 목표

해커톤 평가 기준 'Effective Use of Upstage API'(25점) 점수를 위해 Solar Pro3의 고유 기능 3가지를 활용하도록 LLM 인스턴스를 재구성한다:

1. reasoning_effort 등급 분리: 라우터·평가자는 'high', 질문 생성기는 'low'
2. prompt_cache_key 세션 캐싱: 같은 면접 세션 안에서 이력서·자소서 컨텍스트 재사용
3. 모델 분업: 면접관(질문 생성·평가)은 solar-pro3, 답변 품질 분류기는 solar-mini

각 에이전트의 비즈니스 로직(프롬프트, 구조화 출력 스키마, 폴백 처리 등)은 절대 수정하지 말고, LLM 인스턴스 정의·import·LLM 호출 직전 한 줄만 손댄다.

---

# 작업 1: backend/app/agents/llm.py 를 다음 내용으로 통째로 교체

```python
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
```

---

# 작업 2: 각 에이전트 파일 수정

## 2-1. backend/app/agents/meta.py

(a) import 라인 변경:
- 변경 전: `from app.agents.llm import solar`
- 변경 후: `from app.agents.llm import solar_reasoner as solar, with_session_cache`

(b) 모듈 레벨의 `_router_llm = solar.with_structured_output(RouteDecision)` 정의를 **삭제**한다.

(c) `meta_agent` 함수 내부의 `await _router_llm.ainvoke(...)` 호출 직전에 다음을 삽입하고, 호출 대상을 `router_llm`으로 바꾼다:

```python
llm = with_session_cache(solar, state["session_id"])
router_llm = llm.with_structured_output(RouteDecision)
decision: RouteDecision = await router_llm.ainvoke(
    [("system", SYSTEM_PROMPT), ("human", user_prompt)]
)
```

## 2-2. backend/app/agents/judge.py

(a) import 라인 변경:
- 변경 전: `from app.agents.llm import solar`
- 변경 후: `from app.agents.llm import solar_reasoner as solar, with_session_cache`

(b) 모듈 레벨의 `structured_llm = solar.with_structured_output(JudgeResult)` 정의를 **삭제**한다.

(c) `judge_agent` 함수 내부의 `await structured_llm.ainvoke(...)` 호출을 다음으로 교체:

```python
llm = with_session_cache(solar, state["session_id"])
structured_llm = llm.with_structured_output(JudgeResult)
result: JudgeResult = await structured_llm.ainvoke(
    [("system", SYSTEM_PROMPT), ("human", user_prompt)]
)
```

## 2-3. backend/app/agents/resume.py

(a) import 라인 변경:
- 변경 전: `from app.agents.llm import solar`
- 변경 후: `from app.agents.llm import solar, with_session_cache`

(b) `resume_agent` 함수 내부의 `await solar.ainvoke(...)` 호출을 다음으로 교체:

```python
llm = with_session_cache(solar, state["session_id"])
response = await llm.ainvoke([("system", SYSTEM_PROMPT), ("human", user_prompt)])
```

## 2-4. backend/app/agents/trend.py

(a) import 라인 변경:
- 변경 전: `from app.agents.llm import solar`
- 변경 후: `from app.agents.llm import solar, with_session_cache`

(b) `trend_agent` 함수 내부의 `await solar.ainvoke(...)` 호출을 다음으로 교체:

```python
llm = with_session_cache(solar, state["session_id"])
response = await llm.ainvoke([("system", SYSTEM_PROMPT), ("human", user_prompt)])
```

## 2-5. backend/app/agents/stress.py

(a) import 라인 변경:
- 변경 전: `from app.agents.llm import solar`
- 변경 후: `from app.agents.llm import solar, with_session_cache`

(b) 모듈 레벨의 `_structured_llm = solar.with_structured_output(StressQuestion)` 정의를 **삭제**한다.

(c) `stress_agent` 함수 내부의 try 블록 안의 `await _structured_llm.ainvoke(...)` 호출을 다음으로 교체:

```python
llm = with_session_cache(solar, state["session_id"])
structured_llm = llm.with_structured_output(StressQuestion)
result: StressQuestion = await structured_llm.ainvoke(
    [("system", SYSTEM_PROMPT), ("human", user_prompt)]
)
```

try/except 폴백 구조와 `_is_contextual_question` 후처리는 **절대 건드리지 말 것**.

## 2-6. backend/app/services/answer_quality.py

(a) import 라인 변경:
- 변경 전: `from app.agents.llm import solar`
- 변경 후: `from app.agents.llm import solar_classifier as solar, with_session_cache`

(b) 모듈 레벨의 `_quality_llm = solar.with_structured_output(AnswerQualityResult)` 정의를 **삭제**한다.

(c) `evaluate_answer_quality` 함수 시그니처에 `session_id: str = ""` 파라미터를 추가한다:

```python
async def evaluate_answer_quality(
    question_text: str,
    answer_text: str,
    recent_answers: list[str] | None = None,
    session_id: str = "",
) -> dict:
```

(d) 함수 본문의 try 블록 안의 `await _quality_llm.ainvoke(...)` 호출을 다음으로 교체:

```python
llm = with_session_cache(solar, session_id)
quality_llm = llm.with_structured_output(AnswerQualityResult)
result: AnswerQualityResult = await quality_llm.ainvoke(
    [("system", SYSTEM_PROMPT), ("human", user_prompt)]
)
```

except 폴백 처리(score=55, label='fair' 등)는 **절대 건드리지 말 것**.

---

# 작업 3: 라우터에서 evaluate_answer_quality 호출 시 session_id 전달

## 3-1. backend/app/routers/interview.py

파일 안에서 `evaluate_answer_quality(...)`를 호출하는 모든 지점에 `session_id=state["session_id"]` 키워드 인자를 추가한다.

예시:
```python
quality = await evaluate_answer_quality(
    question_text=latest_question,
    answer_text=body.answer,
    recent_answers=recent_answers,
    session_id=state["session_id"],   # ← 추가
)
```

## 3-2. backend/app/routers/interview_turns.py

같은 패턴으로 `evaluate_answer_quality(...)` 호출 지점에 `session_id=<해당 라우터에서 사용 중인 session_id 변수>` 키워드 인자를 추가한다. 라우터 함수 시그니처에 이미 session_id 파라미터가 있으면 그것을 그대로 사용한다.

---

# 절대 하지 말 것

- resume.py / trend.py / stress.py에서 모델을 solar_reasoner나 solar_classifier로 바꾸지 말 것. 반드시 기본 solar(reasoning_effort='low') 유지
- bind와 with_structured_output의 호출 순서를 절대 바꾸지 말 것 (bind 먼저, with_structured_output 나중)
- 각 에이전트의 시스템 프롬프트, Pydantic 스키마, 폴백 로직, _is_contextual_question 같은 후처리 코드는 한 줄도 수정하지 말 것
- 호출 시그니처 외에 evaluate_answer_quality 함수의 기존 로직 변경 금지
- as solar 별칭을 유지해서 함수 본문 안의 `solar.xxx` 참조가 깨지지 않게 할 것

---

# 작업 완료 후 자체 검증 체크리스트

작업 끝나면 다음을 직접 확인하고 결과를 보고할 것:

1. llm.py에 solar / solar_reasoner / solar_classifier / with_session_cache 4개가 모두 정의되어 있는가
2. meta.py, judge.py의 import에 `solar_reasoner as solar`가 있는가
3. answer_quality.py의 import에 `solar_classifier as solar`가 있는가
4. resume.py, trend.py, stress.py의 import에 `with_session_cache`가 추가되어 있고 기본 solar는 그대로인가
5. meta.py, judge.py, stress.py, answer_quality.py에서 모듈 레벨의 _router_llm / structured_llm / _structured_llm / _quality_llm 정의가 모두 삭제되었는가
6. 5개 에이전트와 evaluate_answer_quality에서 LLM 호출 직전에 with_session_cache(solar, session_id 또는 state["session_id"])가 한 번씩 호출되는가
7. interview.py, interview_turns.py에서 evaluate_answer_quality 호출 시 session_id가 키워드 인자로 전달되는가
8. 각 에이전트의 프롬프트·스키마·폴백·후처리 로직은 그대로인가

위 8개 모두 통과해야 작업 완료. 통과하지 못한 항목이 있으면 명시하고 다시 수정할 것.
`````

---

## 사용 팁

1. **Cursor Composer/Agent 모드** 에서 실행. 일반 Chat 모드는 다파일 수정 약함
2. 실행 후 **diff를 직접 한 번 훑어봐**. 특히 resume/trend/stress의 시스템 프롬프트·폴백 코드가 그대로인지
3. 적용 후 `cd backend && uv run python scripts/demo_interview.py` 돌려서 안 깨지는지 확인
4. 깨지면 에러 메시지 그대로 가져와. 가장 흔한 원인은 `bind` → `with_structured_output` 순서 뒤바뀜이다

작업 끝나면 `agent-demo-result.md`의 `**LLM**: Upstage Solar ('solar-pro')` 부분도 같이 갱신해. 이건 1줄짜리라 Cursor에 별도로 던지지 말고 직접 고치는 게 빠르다.