# AI 모의 면접 에이전트 구현 현황 보고서

## 1. 현재 구현 요약

현재 MVP는 FastAPI 백엔드, LangGraph 기반 에이전트 그래프, SQLite/Redis 저장소, STT/TTS 음성 처리 흐름을 중심으로 구성되어 있다. 사용자는 지원 자료와 채용 정보를 입력하고, 시스템은 이를 면접 세션 컨텍스트로 저장한 뒤 여러 면접 에이전트가 다음 질문을 생성한다.

2026-05-23 현재 워크트리 기준으로 백엔드 코드에는 미커밋 diff가 없고, 본 보고서 문서만 새로 추가된 상태이다. `meta.py`, `helpers.py`, `graph.py`, `interview.py`, `interview_turns.py`, `interview_db.py`는 `py_compile` 검증을 통과했다.

기존 설계상 목표였던 "여러 AI 면접관이 실제 면접처럼 질문을 이어가는 구조"는 현재 코드에서 다음 수준까지 구현되어 있다.

| 영역 | 구현 상태 | 주요 파일 |
|------|----------|----------|
| 세션 생성 및 자료 저장 | 구현됨 | `backend/app/routers/session.py`, `backend/app/routers/interview_sessions.py`, `backend/app/services/interview_db.py` |
| PDF/채용공고 텍스트 처리 | 구현됨 | `backend/app/services/file_parser.py`, `backend/app/services/crawler.py`, `backend/app/routers/interview_sessions.py` |
| 에이전트 상태 모델 | 구현됨 | `backend/app/agents/state.py` |
| 멀티에이전트 그래프 | 구현됨 | `backend/app/services/graph.py` |
| Meta Agent 라우팅 | 구현됨 | `backend/app/agents/meta.py` |
| 서류 기반 질문 Agent | 구현됨 | `backend/app/agents/resume.py` |
| 트렌드 질문 Agent | 구현됨 | `backend/app/agents/trend.py` |
| 압박/꼬리질문 Agent | 구현됨 | `backend/app/agents/stress.py` |
| 최종 평가 Agent | 구현됨 | `backend/app/agents/judge.py` |
| 음성 답변 STT | 구현됨 | `backend/app/services/stt.py` |
| 질문 TTS | 구현됨 | `backend/app/services/tts.py` |
| 음성 턴 DB 기록 | 구현됨 | `backend/app/services/interview_db.py` |
| 음성 턴과 실제 Agent 연결 | 구현됨 | `backend/app/routers/interview_turns.py` |

## 2. 에이전트 구현 상태

### 2.1 Meta Agent

`meta` 에이전트는 면접 흐름을 총괄하는 오케스트레이터 역할을 수행한다. 초기 라운드에서는 이력서 기반 질문으로 시작하고, 이후에는 직전 답변, 대화 기록, 기존 에이전트 호출 이력을 바탕으로 다음 면접관을 선택한다.

현재 선택 가능한 면접관은 다음 세 가지이다.

| Agent | 역할 |
|-------|------|
| `resume` | 이력서, 자기소개서, 포트폴리오 기반 경험 검증 |
| `trend` | 직무, 산업, 회사, 채용공고 기반 트렌드 질문 |
| `stress` | 직전 답변의 약점, 모호함, 논리 부족을 파고드는 꼬리질문 |

`round >= max_rounds` 조건이 만족되면 `judge`로 라우팅해 면접을 종료하고 평가를 생성한다.

### 2.2 Resume Agent

`resume` 에이전트는 사용자의 이력서와 자기소개서를 바탕으로 경험 검증 질문을 생성한다. 모호한 표현, 성과 수치, 의사결정 과정, 본인 기여도를 확인하는 질문을 만들도록 프롬프트가 구성되어 있다.

현재 입력으로 사용하는 데이터는 `resume_text`, `cover_letter`, `messages`이다.

### 2.3 Trend Agent

`trend` 에이전트는 회사, 직무, 채용공고 텍스트를 바탕으로 산업 또는 기술 트렌드 질문을 생성한다. 단순 지식 확인보다 지원자의 의견, 적용 방안, 직무 관점을 묻도록 설계되어 있다.

현재는 채용공고 텍스트 기반 질문 생성까지 구현되어 있으며, 외부 뉴스 RAG 또는 실시간 검색 연동은 아직 고도화 대상이다.

### 2.4 Stress Agent

`stress` 에이전트는 사용자의 직전 답변을 중심으로 약점, 모순, 모호한 표현을 찾아 후속 질문을 생성한다. 실제 면접의 꼬리질문에 가장 가까운 역할을 담당한다.

현재 입력으로 사용하는 데이터는 `last_answer`와 전체 `messages`이다.

### 2.5 Judge Agent

`judge` 에이전트는 면접 종료 시 전체 대화 기록을 읽고 구조화된 평가 결과를 생성한다. 점수는 `overall`, `logic`, `experience`, `trend` 네 축으로 구성된다. LLM 호출 또는 구조화 출력 검증에 실패해도 API가 죽지 않도록 0점 폴백과 실패 메시지를 반환한다.

현재 `judge`는 Redis 기반 텍스트 세션 흐름의 종료 조건에서 호출된다. SQLite 기반 음성 턴 흐름에서는 아직 종료 시점에 `judge`를 직접 호출하는 API가 연결되어 있지 않다.

## 3. 음성 면접 흐름 구현 상태

음성 기반 면접 턴은 `backend/app/routers/interview_turns.py`에서 처리한다.

현재 흐름은 다음과 같다.

```text
사용자 음성 업로드
  -> 음성 파일 저장
  -> OpenAI STT로 transcript 생성
  -> SQLite interview_turns에 질문/답변 저장
  -> 저장된 턴 기록으로 InterviewState 재구성
  -> meta_agent가 다음 면접관 선택
  -> 선택된 resume/trend/stress Agent가 다음 질문 생성
  -> TTS로 질문 음성 생성
  -> transcript, next_question, next_agent_type, tts_audio_url 반환
```

이전 mock 기반 후속 질문 생성 방식에서 벗어나, 현재는 실제 에이전트 노드를 호출해 다음 질문을 생성한다.

음성 흐름에서는 프론트가 종료를 제어하는 전제이기 때문에 `_VOICE_MAX_ROUNDS = 99`로 설정해 `meta`가 중간에 `judge`로 빠지지 않도록 되어 있다. 즉, 음성 턴 API의 책임은 "다음 질문 생성"이며, 최종 평가 리포트 생성은 아직 별도 연결이 필요하다.

## 4. 현재 구현의 장점

- 다중 에이전트 역할이 코드 단위로 분리되어 발표와 시연에서 구조를 설명하기 쉽다.
- `meta`가 단순 라운드로빈이 아니라 대화 맥락 기반으로 다음 에이전트를 선택한다.
- 음성 답변이 STT를 거쳐 실제 에이전트 질문 생성으로 연결된다.
- TTS 폴백 구조가 있어 ElevenLabs 실패 시 OpenAI TTS로 대체할 수 있다.
- 최종 평가 Agent가 구조화 출력 스키마를 사용해 점수와 피드백 형식을 안정화한다.

## 5. 남은 한계

| 한계 | 영향 | 개선 방향 |
|------|------|----------|
| Meta Agent의 선택 이유가 state에 저장되지 않음 | 라우팅 근거를 화면이나 보고서에 보여주기 어려움 | `meta_decisions` 또는 `routing_reason` 필드 추가 |
| Trend Agent의 뉴스 기반 grounding이 약함 | "뉴스 기반 면접관" 차별점이 약해질 수 있음 | 수집 뉴스 제목/요약을 Agent context에 포함 |
| 턴별 정량 평가는 아직 없음 | 면접 중 적응형 난이도 조절 근거가 부족함 | 답변 평가 Agent 또는 간단한 rubric 평가 추가 |
| 음성 흐름과 최종 judge 리포트가 통합되어 있지 않음 | 음성 면접 종료 후 최종 평가 연결이 추가로 필요함 | SQLite turns 기반 judge 호출 API 추가 |
| 문서 분석 결과가 구조화 프로필로 정리되지 않음 | 질문 품질이 긴 텍스트 프롬프트에 의존함 | 경험, 기술, 성과, JD 요구사항을 JSON으로 정규화 |

## 6. 구현 완성도 판단

현재 구현은 해커톤 MVP 기준으로 "멀티에이전트 기반 모의면접"을 설명하고 시연할 수 있는 수준이다. 특히 음성 턴에서 `STT -> meta -> resume/trend/stress -> TTS` 흐름이 연결되어 있어, 단순 챗봇이 아니라 역할 기반 에이전트가 면접 흐름을 조정한다는 점을 보여줄 수 있다.

다만 완성도를 더 높이려면 뉴스 기반 질문의 근거 자료, Meta Agent의 라우팅 근거 저장, 음성 면접 종료 후 judge 평가 연결을 우선 보완하는 것이 좋다.
