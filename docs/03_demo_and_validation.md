# 데모 및 검증 보고서

## 1. 데모 목표

현재 구현의 데모 목표는 "사용자 답변에 따라 여러 AI 면접관이 다음 질문을 생성하는 음성 기반 모의면접"을 보여주는 것이다.

시연에서 반드시 보여줘야 하는 핵심 포인트는 다음과 같다.

- 지원 회사, 직무, 지원 자료가 면접 컨텍스트로 저장된다.
- 면접 질문이 `resume`, `trend`, `stress` 역할에 따라 다르게 생성된다.
- 사용자의 음성 답변이 STT를 거쳐 transcript로 변환된다.
- transcript가 다음 질문 생성에 반영된다.
- TTS로 다음 질문 음성이 생성된다.
- 텍스트 세션 흐름에서는 면접 종료 시 `judge`가 점수와 피드백을 생성할 수 있다.
- 음성 턴 흐름에서는 현재 다음 질문 생성까지 연결되어 있으며, 종료 후 `judge` 평가 API 연결은 남은 작업이다.

## 2. 권장 데모 시나리오

### 2.1 입력 단계

사용자는 다음 정보를 입력한다.

| 입력 | 예시 |
|------|------|
| 회사명 | 토스 |
| 직무명 | 백엔드 개발자 |
| 채용공고 URL | 회사 채용공고 또는 예시 URL |
| 이력서 PDF | 프로젝트 경험이 포함된 이력서 |
| 자기소개서 PDF | 지원 동기와 협업 경험 |
| 포트폴리오 PDF | 프로젝트 상세 내용 |

### 2.2 면접 단계

첫 질문은 이력서/자기소개서 기반 질문으로 시작하는 것이 자연스럽다.

```text
Resume Agent:
지원하신 프로젝트 중 가장 큰 기술적 의사결정이 필요했던 경험을 말씀해 주세요.
```

사용자가 답변하면 다음 턴에서 Meta Agent가 답변의 구체성과 흐름을 보고 다음 면접관을 선택한다.

```text
Stress Agent:
방금 말씀하신 개선 결과에서 본인의 직접적인 기여는 무엇이었고, 그 성과를 어떤 지표로 확인했나요?
```

중간 라운드에서는 회사/직무 기반 질문을 섞는다.

```text
Trend Agent:
최근 백엔드 시스템에서 비용 효율성과 확장성을 동시에 요구하는 흐름이 강해지고 있는데, 지원 직무에서 어떤 기술적 선택이 중요하다고 보시나요?
```

### 2.3 종료 및 평가 단계

텍스트 세션 면접 종료 후 `judge` 에이전트는 전체 대화를 바탕으로 다음 축을 평가한다.

| 평가 축 | 설명 |
|---------|------|
| `overall` | 전체 면접 인상과 종합 점수 |
| `logic` | 답변의 논리성, 근거, 압박 질문 대응력 |
| `experience` | 경험의 구체성, 사실성, 본인 기여도 |
| `trend` | 직무/산업 트렌드 이해도 |

## 3. 현재 검증된 구현 흐름

코드 기준으로 확인 가능한 흐름은 다음과 같다.

| 검증 항목 | 상태 |
|----------|------|
| `meta.py` 문법/import | 통과 |
| `helpers.py` 문법/import | 통과 |
| `graph.py` 문법/import | 통과 |
| `interview.py` 문법/import | 통과 |
| `interview_turns.py` 문법/import | 통과 |
| `interview_db.py` 문법/import | 통과 |
| 음성 턴에서 mock 제거 | 반영됨 |
| 음성 턴에서 실제 `meta_agent` 호출 | 반영됨 |
| 음성 턴에서 선택된 질문 Agent 호출 | 반영됨 |
| STT 실패 시 안전 응답 | 반영됨 |
| 다음 질문 생성 실패 시 폴백 질문 | 반영됨 |
| TTS 실패 시 URL 없이 응답 | 반영됨 |

## 4. 데모 전 체크리스트

### 4.1 환경 변수

```bash
UPSTAGE_API_KEY=
OPENAI_API_KEY=
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=
```

필수 키는 `UPSTAGE_API_KEY`와 `OPENAI_API_KEY`이다. ElevenLabs 키가 없어도 OpenAI TTS fallback을 사용할 수 있다.

### 4.2 백엔드 실행

```bash
cd backend
uv sync
uv run uvicorn main:app --reload
```

확인 URL:

```text
http://localhost:8000/health
http://localhost:8000/docs
```

### 4.3 Redis

텍스트 세션 API는 Redis를 사용한다.

```bash
brew services start redis
```

### 4.4 SQLite

음성 턴 API는 `backend/app/data/interview.db`를 사용한다. 서버 시작 시 `init_interview_db()`가 테이블을 생성한다.

## 5. 리스크와 대응

| 리스크 | 증상 | 대응 |
|--------|------|------|
| Upstage API 키 누락 | 질문 생성 실패 | `.env`의 `UPSTAGE_API_KEY` 확인 |
| OpenAI API 키 누락 | STT/TTS 실패 | `.env`의 `OPENAI_API_KEY` 확인 |
| Redis 미실행 | `/api/v1/session` 흐름 실패 | `brew services start redis` |
| 음성 인식 실패 | transcript 빈 값 | 프론트에서 재녹음 안내 |
| LLM 구조화 출력 실패 | meta 또는 judge 실패 | 현재 fallback 동작 사용 |
| 뉴스 기반 질문 약함 | 트렌드 질문이 일반론으로 보임 | 시연 시 채용공고 텍스트를 충분히 넣기 |

## 6. 발표용 구현 설명 문장

> 본 시스템은 사용자의 지원 자료와 채용공고를 기반으로 면접 상태를 구성하고, Meta Agent가 직전 답변과 전체 대화 맥락을 분석해 다음 면접관을 선택합니다. 선택된 Resume, Trend, Stress Agent는 각각 서류 검증, 산업/직무 트렌드, 꼬리질문 역할을 맡아 질문을 생성합니다. 사용자의 음성 답변은 STT로 텍스트화되어 다음 질문 생성에 반영되고, 생성된 질문은 TTS를 통해 다시 음성으로 출력됩니다. 텍스트 세션 흐름에서는 면접 종료 후 Judge Agent가 전체 대화를 평가해 점수와 종합 피드백을 제공합니다.

## 7. 다음 개선 제안

데모 완성도를 높이기 위한 우선순위는 다음과 같다.

1. 음성 면접 종료 버튼에서 `judge` 평가를 호출하는 API 연결
2. Trend Agent에 최근 뉴스 요약 context 추가
3. Meta Agent의 라우팅 이유를 저장하고 화면에 표시
4. 질문별 답변 평가를 저장해 최종 리포트의 근거로 사용
5. 포트폴리오/이력서 파싱 결과를 구조화 JSON으로 정리
