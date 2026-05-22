# 에이전트 플로우 상세 문서

## 1. 전체 아키텍처

현재 시스템은 두 가지 면접 흐름을 가진다.

| 흐름 | 설명 | 주요 저장소 |
|------|------|------------|
| 텍스트 세션 흐름 | Redis 세션에 `InterviewState`를 저장하고 LangGraph 전체 그래프를 실행 | Redis |
| 음성 턴 흐름 | SQLite에 각 턴을 저장하고, 저장된 턴으로 state를 재구성해 다음 질문 생성 | SQLite |

텍스트 세션 흐름은 `meta`, `resume`, `trend`, `stress`, `judge` 전체를 사용한다. 음성 턴 흐름은 현재 다음 질문 생성을 위해 `meta`, `resume`, `trend`, `stress`를 사용하며, `judge` 기반 최종 평가는 아직 별도 API로 연결되어 있지 않다.

## 2. LangGraph 기반 텍스트 면접 흐름

텍스트 세션 API는 `backend/app/routers/interview.py`에 구현되어 있다.

```text
POST /api/v1/session/{session_id}/start
  -> 초기 InterviewState 생성
  -> build_interview_graph().ainvoke(state)
  -> meta가 resume 선택
  -> resume이 첫 질문 생성
  -> Redis session.interview_state 저장

POST /api/v1/session/{session_id}/answer
  -> candidate 답변을 messages에 append
  -> last_answer 갱신
  -> round 증가
  -> graph 실행
  -> meta가 다음 agent 선택
  -> 선택 agent가 질문 생성 또는 judge가 평가 생성
  -> Redis session.interview_state 저장

GET /api/v1/session/{session_id}/report
  -> done 상태 확인
  -> scores, feedback, messages, agent_history 반환
```

LangGraph 구조는 다음과 같다.

```text
meta
  -> resume -> END
  -> trend  -> END
  -> stress -> END
  -> judge  -> END
```

각 API 호출마다 그래프를 한 번 실행해 "이번 턴의 다음 질문"을 생성하는 방식이다.

## 3. 음성 기반 면접 턴 흐름

음성 턴 API는 `backend/app/routers/interview_turns.py`에 구현되어 있다.

```text
POST /api/interview-sessions/{session_id}/turns/audio
```

처리 단계는 다음과 같다.

1. 업로드된 음성 파일을 `backend/app/uploads/audio/`에 저장한다.
2. `transcribe_audio()`로 한국어 STT를 수행한다.
3. 이번 턴의 질문, 답변 transcript, agent_type, audio_path를 SQLite `interview_turns`에 저장한다.
4. `get_turns()`와 `get_agent_context()`로 SQLite의 턴 기록과 agent context를 읽어 `InterviewState`를 복원한다.
5. `meta_agent()`가 다음 면접관을 선택한다.
6. 선택된 `resume_agent`, `trend_agent`, `stress_agent` 중 하나가 다음 질문을 생성한다.
7. `synthesize_speech()`로 다음 질문의 TTS 파일을 생성한다.
8. 프론트에 `transcript`, `next_question`, `next_agent_type`, `tts_audio_url`을 반환한다.

음성 턴 흐름에서 `_VOICE_MAX_ROUNDS`는 99로 설정되어 있다. 이는 음성 면접의 종료를 프론트가 제어한다는 전제 때문에, 일반 턴 진행 중 `meta`가 `judge`로 라우팅되지 않도록 하기 위한 장치이다.

## 4. InterviewState 필드 의미

| 필드 | 의미 |
|------|------|
| `session_id` | 면접 세션 ID |
| `cover_letter` | 자기소개서 텍스트 |
| `resume_text` | 이력서 텍스트 |
| `portfolio_text` | 포트폴리오 텍스트 |
| `company` | 지원 회사 |
| `role` | 지원 직무 |
| `job_posting_text` | 채용공고 텍스트 |
| `round` | 현재 라운드 번호 |
| `max_rounds` | 최대 라운드 수. 텍스트 흐름은 기본 8, 음성 턴 흐름은 99 |
| `messages` | 면접관/지원자 대화 기록 |
| `agent_history` | 지금까지 호출된 에이전트 순서 |
| `current_agent` | 이번 턴에서 선택된 에이전트 |
| `current_question` | 이번 턴에서 생성된 질문 |
| `last_answer` | 지원자의 직전 답변 |
| `is_done` | 면접 종료 여부 |
| `scores` | judge 평가 점수 |
| `feedback` | judge 종합 피드백 |

## 5. Meta Agent 라우팅 기준

현재 `meta` 에이전트는 Solar Pro 기반 구조화 출력을 사용해 다음 에이전트를 선택한다.

선택 규칙은 프롬프트에 다음처럼 정의되어 있다.

- 직전 답변이 모호하거나 근거가 부족하면 `stress`
- 세 유형을 고르게 다루되, 아직 안 쓴 유형 우선 고려
- `trend`는 면접당 1~2회 수준으로 제한
- 첫 질문은 `resume`으로 시작
- `round >= max_rounds`이면 `judge`로 종료

구조화 출력 스키마는 다음과 같다.

```text
RouteDecision
  - next_agent: resume | trend | stress
  - reason: string
```

현재 `reason`은 받아오지만 state에 저장하지 않는다. 향후 리포트나 디버깅 화면에서 라우팅 근거를 보여주려면 저장 필드가 필요하다.

## 6. Agent별 프롬프트 역할

| Agent | 주요 입력 | 질문 방향 |
|-------|----------|----------|
| `resume` | 이력서, 자기소개서, 대화 기록 | 경험 검증, 수치, 역할, 의사결정 과정 |
| `trend` | 회사, 직무, 채용공고 | 산업/기술 트렌드에 대한 의견과 적용 |
| `stress` | 직전 답변, 대화 기록 | 모호함, 논리 약점, 근거 부족 꼬리질문 |
| `judge` | 전체 대화 기록 | 종합 점수, 논리성, 경험 구체성, 트렌드 이해도, 피드백 |

## 7. 발표 시 강조할 수 있는 구현 포인트

- 질문 생성이 하나의 프롬프트가 아니라 역할별 에이전트로 분리되어 있다.
- Meta Agent가 직전 답변과 대화 히스토리를 보고 다음 질문 유형을 선택한다.
- 음성 답변이 STT 이후 실제 에이전트 상태에 반영되어 다음 질문으로 이어진다.
- 텍스트 세션의 최종 평가는 구조화 출력으로 점수와 피드백 형식을 고정한다.
- 음성 턴은 현재 다음 질문 생성까지 실제 에이전트와 연결되어 있으며, 종료 후 평가 연결은 후속 작업이다.

## 8. 고도화 우선순위

1. 음성 면접 종료 후 SQLite turns를 기반으로 `judge`를 호출하는 최종 리포트 API 추가
2. `meta`의 `reason`을 저장해 라우팅 근거를 리포트에 포함
3. 뉴스 수집 결과를 `trend` context에 넣어 뉴스 기반 질문 강화
4. 문서 파싱 결과를 구조화된 지원자 프로필로 변환
5. 턴별 답변 평가를 추가해 난이도와 꼬리질문 강도 조절
