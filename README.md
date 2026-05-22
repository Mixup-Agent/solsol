# AI 모의 면접 에이전트 시스템

> 자소서, 이력서, 포트폴리오, 채용공고를 바탕으로 실제 면접처럼 질문과 꼬리질문을 이어가는 음성 기반 AI 모의면접 서비스

Upstage Solar Pro AI Agent 해커톤 출품작입니다. 사용자의 지원 자료와 채용 정보를 분석해 개인화된 면접 질문을 생성하고, 음성 답변을 기반으로 다음 질문과 최종 피드백을 제공하는 **LangGraph 기반 멀티에이전트 시스템**입니다.

## 프로젝트 정보

| 항목 | 내용 |
|------|------|
| 작품명 | AI 모의 면접 에이전트 시스템 |
| 팀명 | 솔솔(solsol) |
| 팀원 | 김나경, 박민영, 유지예, 이정연 |
| 핵심 모델 | Upstage Solar Pro |
| 주요 형태 | 웹 기반 음성 모의면접 서비스 |
| 형식 | Solar Pro AI Agent 해커톤 무박 2일 MVP |

## 아이디어 배경

최근 면접은 단순한 질문 답변이 아니라 지원자의 경험, 직무 이해도, 문제 해결력, 커뮤니케이션 능력을 종합적으로 평가하는 과정입니다. 하지만 취업 준비자는 자소서, 이력서, 포트폴리오, 채용공고를 바탕으로 예상 질문을 준비하더라도 실제 면접처럼 즉흥적인 질문과 꼬리질문에 대응하는 연습을 하기 어렵습니다.

이 프로젝트는 사용자의 지원 자료와 채용공고를 분석하고, 여러 AI 면접관이 역할을 나누어 실제 면접처럼 질문을 이어가는 모의면접 환경을 제공합니다. 면접 종료 후에는 질문과 답변 기록을 기반으로 강점과 개선점을 정리한 피드백 리포트를 제공합니다.

## 핵심 기능

| 기능 | 설명 |
|------|------|
| 지원 자료 입력 | 자소서·이력서·포트폴리오 PDF, 회사명, 직무명, 채용공고 링크 입력 |
| 문서·공고 분석 | Upstage Document Parse로 PDF 구조화, 채용공고 HTML 크롤링 |
| 다중 AI 면접관 | 이력서, 트렌드, 압박/꼬리질문, 총괄, 평가 5개 에이전트가 협력 |
| 음성 면접 | OpenAI STT로 음성 답변 인식, ElevenLabs/OpenAI TTS로 면접관 음성 출력 |
| 동적 꼬리질문 | 답변에서 모호함·근거 부족·구체성 부족을 찾아 후속 질문 생성 |
| 답변 품질 평가 | 매 답변마다 별도 평가해 다음 면접관 라우팅의 근거로 활용 |
| 최종 피드백 | 종합·논리·경험·트렌드 점수와 한국어 종합 피드백 제공 |

## 서비스 흐름

LangGraph StateGraph(`backend/app/services/graph.py`)가 다음 단계를 조율합니다. 모든 라운드의 라우팅 결정은 `meta_decisions`에 누적되어 발표·디버깅용으로 보존됩니다.

1. **세션 생성** — `POST /api/v1/interview-sessions` → PDF 3종을 Upstage Document Parse로 구조화, 채용공고 URL은 HTML 크롤링, 전체 컨텍스트를 SQLite `agent_contexts`에 저장
2. **첫 질문 생성** — `POST .../turns/first` → meta가 round 0으로 인식해 resume 에이전트 선택, 이력서 기반 오프닝 질문 + TTS
3. **음성 답변 처리** — `POST .../turns/audio` → 오디오 저장 → OpenAI STT 전사 → 답변 품질 평가 → `interview_turns` 테이블 영속화
4. **다음 면접관 선택** — meta가 직전 답변·대화·답변 품질을 종합해 `resume`/`trend`/`stress` 중 적응적으로 라우팅
5. **꼬리/검증 질문 생성** — 선택된 에이전트가 Solar Pro로 질문 생성 → TTS 음성 출력
6. **(반복)** 3~5단계를 max_rounds(기본 8)까지 반복
7. **최종 평가** — round ≥ max_rounds 도달 시 meta가 judge로 라우팅, judge가 전체 대화를 구조화 출력으로 평가
8. **리포트 제공** — `GET .../report` → 종합 점수 + 세부 점수 + 종합 피드백을 프론트 ReportScreen에 표시

```text
사용자 입력 (자소서·이력서·포트폴리오·회사·직무·채용공고 URL)
        |
        v
문서·공고 분석 (Upstage Document Parse + HTML 크롤링)
        |
        v
AI 모의면접 루프 (Meta -> Resume/Trend/Stress -> STT/TTS, 라운드 반복)
        |
        v
최종 평가 (Judge가 점수와 한국어 피드백 생성)
```

## 멀티에이전트 구조

LangGraph 기반 5개 노드로 구성되며, `meta`가 총괄, 나머지 4개가 전문 역할을 맡습니다.

| Agent | 역할 | 활용 데이터 |
|-------|------|------------|
| `meta` | 총괄 오케스트레이터. 직전 답변·대화·답변 품질을 보고 다음 면접관을 적응적으로 선택. 선택 이유 기록 + `trend` 횟수 캡(2회) 등 정책 관리 | agent_history, last_answer, answer_quality_history |
| `resume` | 이력서·자소서·포트폴리오 기반 경험 검증 질문 생성. 모호한 표현을 수치·사례로 파고듦 | resume_text, cover_letter |
| `trend` | 직무·산업 트렌드 질문 생성. 단순 지식 확인이 아니라 의견·적용 방안을 묻는 형태 | role, company, job_posting_text |
| `stress` | 직전 답변의 약점·모순·모호함을 파고드는 압박·꼬리질문 생성 | last_answer, messages |
| `judge` | 면접 종료 시 전체 대화 평가. Solar 구조화 출력으로 4축 점수 + 종합 피드백 생성. 실패 시 0점 폴백 | 전체 messages, role, company |

```text
                 +----------------+
                 |   Meta Agent   |
                 +--------+-------+
                          |
          +---------------+---------------+
          |               |               |
          v               v               v
   +-------------+ +-------------+ +-------------+
   | Resume      | | Trend       | | Stress      |
   | Agent       | | Agent       | | Agent       |
   +-------------+ +-------------+ +-------------+
          |               |               |
          +---------------+---------------+
                          |
                          v
                 +----------------+
                 |  Judge Agent   |
                 +----------------+
```

## 핵심 로직

세 가지 핵심 결정·점수는 모두 명시적인 룰 또는 구조화된 LLM 출력으로 산출됩니다.

### 적응형 라우팅 — `meta.py`

LLM이 직전 답변·대화 흐름·답변 품질을 보고 다음 면접관을 선택하되, 안전 정책을 함께 적용합니다.

```
1. round >= max_rounds        → judge (면접 종료)
2. round == 0 or messages 없음 → resume (이력서 기반 오프닝)
3. 그 외                       → LLM 라우팅 (RouteDecision 구조화 출력)
   - 직전 답변 부실 → stress (꼬리질문)
   - 미사용 유형 우선 (균형)
4. 폴백: LLM 실패 시 agent_history 최소 사용 에이전트 선택
5. 하드 캡: trend가 이미 2회 사용됐으면 resume/stress로 강제 대체
```

### 답변 품질 평가 — `answer_quality.py`

매 음성 답변마다 별도로 평가해 `interview_turns.answer_quality_json`에 저장합니다. 평가 결과(`score`/`label`/`flags`/`action_hint`)는 meta가 다음 면접관 선택 시 근거로 활용됩니다 (예: 수치 부족 → stress로 라우팅).

### 최종 평가 — `judge.py`

전체 대화를 Solar에 `with_structured_output(JudgeResult)`로 호출해 JSON 스키마를 강제합니다.

```
JudgeResult: {
    overall: 0~100,      # 종합 인상 점수
    logic: 0~100,        # 논리적 일관성 + 압박 대응력
    experience: 0~100,   # 이력서 기반 답변 구체성
    trend: 0~100,        # 트렌드 통찰력
    feedback: str        # 3~5문장 종합 피드백
}
```

LLM 또는 스키마 검증 실패 시 0점 폴백으로 리포트 엔드포인트가 죽지 않게 보장합니다.

## Upstage Solar Pro 활용

Solar Pro는 본 서비스의 핵심 LLM 엔진으로, 사용자의 입력 자료를 이해하고, 면접 질문을 생성하며, 답변 맥락에 맞는 후속 질문과 최종 평가를 구성합니다. 추가로 PDF 구조화에 **Upstage Document Parse**를 함께 활용합니다.

| 활용 위치 | 활용 방식 |
|----------|----------|
| 입력 자료 기반 질문 | 자소서·이력서·포트폴리오에서 역할, 문제 상황, 해결 과정, 성과를 파악해 직무 적합성 질문 생성 |
| 꼬리질문 생성 | 답변에서 구체적 수치, 본인 기여도, 의사결정 근거가 부족한 부분을 찾아 후속 질문 생성 |
| 총괄 라우팅 | 전체 대화 맥락과 답변 품질을 바탕으로 다음 면접관 유형·종료 여부 판단 |
| 평가 리포트 | 면접 전체 대화를 분석해 종합·논리·경험·트렌드 점수와 피드백을 구조화 출력으로 생성 |
| 문서 구조화 | Document Parse로 PDF를 텍스트/마크다운/HTML로 변환해 컨텍스트화 |

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| 프론트엔드 | React 19, Vite, TanStack Router, Tailwind CSS, Radix UI |
| 백엔드 | FastAPI, Python 3.11, Pydantic |
| 에이전트 | LangGraph (StateGraph), langchain-upstage (ChatUpstage) |
| LLM | Upstage Solar Pro (`solar-pro`) |
| 문서 처리 | Upstage Document Parse, pdfplumber (폴백) |
| 채용공고 수집 | httpx, BeautifulSoup |
| 음성 처리 | OpenAI STT (`gpt-4o-mini-transcribe`), ElevenLabs TTS (주), OpenAI TTS (`gpt-4o-mini-tts`) 폴백 |
| 저장소 | SQLite (세션·문서·면접 턴·답변 품질), Redis (텍스트 흐름 세션) |
| 의존성 관리 | uv (`pyproject.toml` + `uv.lock`) |

## 저장소 구조

```text
shipyak/
├── backend/                          # FastAPI 백엔드와 멀티에이전트 로직
│   ├── main.py                       # 앱 진입점 (라우터 등록, lifespan)
│   ├── pyproject.toml / uv.lock      # 의존성 관리 (uv)
│   ├── scripts/
│   │   └── demo_interview.py         # LangGraph E2E 데모
│   └── app/
│       ├── config.py                 # 환경변수 (절대경로 .env 자동 로딩)
│       ├── agents/                   # LangGraph 에이전트
│       │   ├── llm.py                #   공용 Solar 인스턴스
│       │   ├── helpers.py            #   transcript 포맷·답변 정리
│       │   ├── state.py              #   InterviewState (TypedDict)
│       │   ├── meta.py               #   총괄 오케스트레이터 (적응형 라우팅)
│       │   ├── resume.py             #   이력서 기반 질문
│       │   ├── trend.py              #   직무·산업 트렌드 질문
│       │   ├── stress.py             #   압박·꼬리질문
│       │   └── judge.py              #   최종 평가 (구조화 출력)
│       ├── services/
│       │   ├── graph.py              #   LangGraph StateGraph 빌드
│       │   ├── interview_db.py       #   SQLite 저장소
│       │   ├── session_store.py      #   Redis (텍스트 흐름)
│       │   ├── stt.py / tts.py       #   음성 처리
│       │   ├── answer_quality.py     #   답변 품질 평가
│       │   ├── file_parser.py        #   Upstage Document Parse 래퍼
│       │   └── crawler.py            #   채용공고 HTML 크롤링
│       ├── routers/
│       │   ├── session.py / interview.py                  # 텍스트 면접 흐름
│       │   └── interview_sessions.py / interview_turns.py # 음성 면접 흐름
│       └── models/                   # Pydantic 스키마
├── lovable/                          # 웹 프론트엔드
│   └── src/
│       ├── routes/index.tsx          # 메인 (stage 상태 관리)
│       ├── components/interview/     # 5개 화면 컴포넌트
│       ├── lib/api.ts                # 백엔드 API 클라이언트
│       └── assets/interviewers/      # 면접관 아바타 4종
├── docs/                             # 설계·구현 현황 문서
└── data/, design/, presentation/     # 데이터·디자인·발표 자료
```

## 시작하기

### 1. 백엔드 환경 설정

의존성은 [uv](https://docs.astral.sh/uv/)로 관리합니다. (uv 미설치 시 `curl -LsSf https://astral.sh/uv/install.sh | sh`)

```bash
cd backend
uv sync                           # uv.lock 기준 .venv 자동 동기화
cp .env.example .env              # 키 입력은 아래 참고
```

### 2. API 키 설정

| 환경변수 | 용도 | 필수 여부 |
|----------|------|-----------|
| `UPSTAGE_API_KEY` | Solar Pro (5개 에이전트) + Document Parse | **필수** |
| `OPENAI_API_KEY` | STT(`gpt-4o-mini-transcribe`) + TTS(`gpt-4o-mini-tts`) | **필수** (음성 사용 시) |
| `ELEVENLABS_API_KEY` | TTS 주 채널. 없으면 OpenAI TTS로 폴백 | 선택 |
| `ELEVENLABS_VOICE_ID` | ElevenLabs 보이스 ID | 선택 |
| `REDIS_URL` | 텍스트 면접 세션 저장소 (기본 `redis://localhost:6379`) | 선택 |

### 3. Redis 실행 (텍스트 면접 흐름 사용 시)

```bash
brew install redis
brew services start redis
```

### 4. 백엔드 실행

```bash
cd backend
uv run uvicorn main:app --reload
```

- API 문서: <http://localhost:8000/docs>
- 헬스체크: <http://localhost:8000/health>

### 5. 프론트엔드 실행

```bash
cd lovable
bun install        # 또는 npm install
bun dev            # 또는 npm run dev
```

### 6. 데모 스크립트 (서버·프론트 없이)

```bash
cd backend
uv run python scripts/demo_interview.py
```

LangGraph 파이프라인이 콘솔에 처음부터 끝까지 출력됩니다.

## 주요 API

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/api/v1/interview-sessions` | 세션 생성 (PDF 3종 업로드 + 회사·직무·채용공고 URL) |
| `POST` | `/api/v1/interview-sessions/{id}/turns/first` | 면접 첫 질문 생성 + TTS |
| `POST` | `/api/v1/interview-sessions/{id}/turns/audio` | 음성 답변 업로드 → STT + 품질 평가 + 다음 질문 + TTS |
| `POST` | `/api/v1/session` | 텍스트 흐름 세션 생성 |
| `POST` | `/api/v1/session/{id}/start` | 텍스트 면접 시작 및 첫 질문 |
| `POST` | `/api/v1/session/{id}/answer` | 텍스트 답변 제출 후 다음 질문 |
| `GET` | `/api/v1/session/{id}/report` | 최종 평가 리포트 (scores + feedback + 전체 대화) |
| `GET` | `/health` | 서버 및 Redis 상태 확인 |

## 차별점

- 단순 예상 질문 제공이 아니라 **답변에 따라 질문 흐름이 바뀌는 동적 면접 경험**
- 자소서·이력서·포트폴리오·채용공고를 함께 분석한 개인화 질문
- 여러 AI 면접관이 역할을 나누고, **meta가 답변 품질을 보고 적응적으로 다음 면접관을 선택**
- 텍스트 챗봇이 아닌 **음성 기반 면접 흐름**으로 실전 긴장감과 몰입감 제공
- 면접 종료 후 **정량 점수와 정성 피드백**을 함께 제공해 복습·개선 가능

## 설계 원칙

- **얇은 오케스트레이터** — meta는 라우팅만 담당, 실제 질문·평가는 각 전문 Agent가 수행
- **적응형 라우팅** — round-robin이 아니라 직전 답변·대화·답변 품질을 보고 LLM이 다음 면접관을 선택, 이유를 `meta_decisions`에 기록
- **구조화 출력 우선** — judge·meta 라우팅 모두 `with_structured_output`으로 스키마를 강제, 수동 JSON 파싱 위험 제거
- **폴백 우선** — LLM·STT·TTS·크롤링 실패 시 0점 폴백·기본 질문·빈 결과로 데모 중단 방지
- **정책 가드** — trend 면접관은 면접당 최대 2회로 하드 캡 (LLM이 한쪽 유형만 고르는 것을 차단)
- **턴 영속화** — 음성 답변·전사·품질 평가를 SQLite에 누적해 면접 재구성·리포트 생성·재시청 가능
- **API 키 보안** — 외부 키는 `.env`로 관리하고 절대경로 기반 자동 로딩으로 실행 폴더와 무관하게 동작

## 기대 효과

취업 준비자는 고비용 면접 컨설팅 없이도 실제 면접과 유사한 환경에서 반복 연습할 수 있습니다. 특히 개인의 지원 자료와 지원 직무를 반영한 질문을 받을 수 있어 일반적인 예상 질문보다 실전 대응력을 높일 수 있습니다.

향후에는 직무별 전문 면접관, 기업별 면접 스타일, 면접 리포트 PDF, 답변 개선 예시, 실시간 발화 습관 분석 등으로 확장할 수 있습니다.

## 참고 문서

- [Interview Agent 빠른 시작](docs/interview-agent.md)
- [AI 모의 면접 에이전트 개요(초기 설계)](docs/interview-agent-overview.md)
- [Upstage API 명세](docs/upstage-api-spec.md)
