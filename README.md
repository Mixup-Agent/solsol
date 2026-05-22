# AI 모의 면접 에이전트 시스템

> 자소서, 이력서, 포트폴리오, 채용공고를 바탕으로 실제 면접처럼 질문과 꼬리질문을 이어가는 음성 기반 AI 모의면접 서비스

Upstage Solar Pro3 AI Agent 해커톤 출품작입니다. 사용자의 지원 자료와 채용 정보를 분석해 개인화된 면접 질문을 생성하고, 음성 답변을 기반으로 다음 질문과 최종 피드백을 제공하는 멀티에이전트 시스템입니다.

## 프로젝트 정보

| 항목 | 내용 |
|------|------|
| 작품명 | AI 모의 면접 에이전트 시스템 |
| 팀명 | 솔솔(solsol) |
| 팀원 | 김나경, 박민영, 유지예, 이정연 |
| 핵심 모델 | Upstage Solar Pro3 |
| 주요 형태 | 웹 기반 음성 모의면접 서비스 |

## 아이디어 배경

최근 면접은 단순한 질문 답변이 아니라 지원자의 경험, 직무 이해도, 문제 해결력, 커뮤니케이션 능력을 종합적으로 평가하는 과정입니다. 하지만 취업 준비자는 자소서, 이력서, 포트폴리오, 채용공고를 바탕으로 예상 질문을 준비하더라도 실제 면접처럼 즉흥적인 질문과 꼬리질문에 대응하는 연습을 하기 어렵습니다.

이 프로젝트는 사용자의 지원 자료와 채용공고를 분석하고, 여러 AI 면접관이 역할을 나누어 실제 면접처럼 질문을 이어가는 모의면접 환경을 제공합니다. 면접 종료 후에는 질문과 답변 기록을 기반으로 강점과 개선점을 정리한 피드백 리포트를 제공합니다.

## 핵심 기능

| 기능 | 설명 |
|------|------|
| 지원 자료 입력 | 자소서, 이력서, 포트폴리오 PDF, 회사명, 직무명, 채용공고 링크를 입력합니다. |
| 문서 및 채용공고 분석 | PDF와 채용공고에서 핵심 경험, 프로젝트, 직무 역량, 회사 정보를 추출합니다. |
| 다중 AI 면접관 | 이력서 기반, 뉴스/트렌드 기반, 꼬리질문/압박 질문, 총괄 평가 에이전트가 면접을 진행합니다. |
| 음성 면접 | 사용자의 음성 답변을 STT로 텍스트화하고, 생성된 질문을 TTS 음성으로 출력합니다. |
| 동적 꼬리질문 | 사용자의 답변에서 모호한 부분, 근거 부족, 구체성 부족을 찾아 후속 질문을 생성합니다. |
| 최종 피드백 | 전체 대화를 바탕으로 논리성, 경험 구체성, 트렌드 이해도, 종합 점수와 피드백을 제공합니다. |

## 서비스 흐름

```text
사용자 입력
  자소서 / 이력서 / 포트폴리오 PDF / 회사명 / 직무명 / 채용공고 URL
        |
        v
문서 및 공고 분석
  PDF 파싱, 채용공고 크롤링, 핵심 경험 및 직무 요구사항 추출
        |
        v
AI 모의면접 루프
  Meta Agent -> Resume Agent / Trend Agent / Stress Agent -> STT/TTS
        |
        v
최종 평가
  Judge Agent가 점수와 한국어 피드백 리포트 생성
```

## 멀티에이전트 구조

현재 구현은 LangGraph 기반의 5개 노드로 구성됩니다.

| Agent | 역할 |
|-------|------|
| `meta` | 전체 면접 흐름 제어, 다음 질문 유형 선택, 종료 여부 판단 |
| `resume` | 이력서, 자소서, 포트폴리오 기반 경험 검증 질문 생성 |
| `trend` | 회사, 직무, 채용공고, 산업/기술 트렌드 기반 질문 생성 |
| `stress` | 사용자의 직전 답변을 분석해 압박 질문과 꼬리질문 생성 |
| `judge` | 전체 면접 대화를 평가하고 점수 및 종합 피드백 생성 |

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

## Upstage Solar Pro3 활용

Solar Pro3는 본 서비스의 핵심 LLM 엔진으로 활용됩니다. 사용자의 입력 자료를 이해하고, 면접 질문을 생성하며, 답변 맥락에 맞는 후속 질문과 최종 평가를 구성하는 데 사용합니다.

| 활용 위치 | 활용 방식 |
|----------|----------|
| 입력데이터 기반 질문 | 자소서, 이력서, 포트폴리오에서 역할, 문제 상황, 해결 과정, 성과를 파악해 직무 적합성 질문을 생성합니다. |
| 꼬리질문 생성 | 답변에서 구체적 수치, 본인 기여도, 의사결정 근거가 부족한 부분을 찾아 후속 질문을 만듭니다. |
| 총괄 Agent | 전체 대화 맥락을 바탕으로 다음 질문 유형, 난이도, 종료 여부를 판단합니다. |
| 평가 리포트 | 면접 전체 대화를 분석해 논리성, 경험 구체성, 트렌드 이해도, 종합 피드백을 생성합니다. |

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| 프론트엔드 | React, Vite, TanStack Router, Tailwind CSS, Radix UI |
| 백엔드 | FastAPI, Python 3.11, Pydantic |
| Agent | LangGraph, LangChain Upstage, Upstage Solar Pro3 |
| 문서 처리 | pdfplumber, Upstage Document Parse/Information Extract 활용 가능 |
| 채용공고 수집 | httpx, BeautifulSoup |
| 음성 처리 | OpenAI STT, ElevenLabs TTS, OpenAI TTS fallback |
| 저장소 | Redis 세션 저장소, SQLite 인터뷰 기록 |

## 저장소 구조

```text
shipyak/
├── backend/                 # FastAPI 백엔드와 멀티에이전트 로직
│   ├── main.py              # API 엔트리포인트
│   ├── app/
│   │   ├── agents/          # meta, resume, trend, stress, judge Agent
│   │   ├── routers/         # 세션, 면접, 턴 기록 API
│   │   ├── services/        # STT, TTS, PDF 파싱, 크롤링, 그래프, 저장소
│   │   └── models/          # Pydantic 모델
│   └── scripts/             # 데모 및 데이터 수집 스크립트
├── lovable/                 # 웹 프론트엔드
│   └── src/
│       ├── components/interview/
│       ├── routes/
│       └── assets/interviewers/
├── docs/                    # 설계 문서와 API/에이전트 문서
├── data/                    # 데이터 수집 및 전처리 자료
├── design/                  # 디자인 에셋
└── presentation/            # 발표 자료
```

## 시작하기

### 1. 백엔드 환경 설정

```bash
cd backend
uv sync
cp .env.example .env
```

`.env`에 필요한 API 키를 입력합니다.

```bash
UPSTAGE_API_KEY=
OPENAI_API_KEY=
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=
```

### 2. Redis 실행

```bash
brew install redis
brew services start redis
```

### 3. 백엔드 실행

```bash
cd backend
uv run uvicorn main:app --reload
```

- API 문서: http://localhost:8000/docs
- 헬스체크: http://localhost:8000/health

### 4. 프론트엔드 실행

```bash
cd lovable
npm install
npm run dev
```

## 주요 API

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/api/v1/session` | 지원 자료 업로드 및 면접 세션 생성 |
| `GET` | `/api/v1/session/{id}` | 세션 조회 |
| `POST` | `/api/v1/session/{id}/start` | 면접 시작 및 첫 질문 생성 |
| `POST` | `/api/v1/session/{id}/answer` | 답변 제출 후 다음 질문 생성 |
| `GET` | `/api/v1/session/{id}/report` | 최종 피드백 리포트 조회 |
| `GET` | `/health` | 서버 및 Redis 상태 확인 |

## 차별점

- 단순 예상 질문 제공이 아니라 답변에 따라 질문 흐름이 바뀌는 동적 면접 경험을 제공합니다.
- 자소서, 이력서, 포트폴리오, 채용공고를 함께 분석해 개인화된 질문을 생성합니다.
- 여러 AI 면접관이 역할을 나누어 실제 면접처럼 질문 관점을 전환합니다.
- 텍스트 챗봇이 아닌 음성 기반 면접 흐름을 제공해 실전과 유사한 긴장감과 몰입감을 만듭니다.
- 면접 종료 후 정량 점수와 정성 피드백을 함께 제공해 복습과 개선이 가능합니다.

## 기대 효과

취업 준비자는 고비용 면접 컨설팅 없이도 실제 면접과 유사한 환경에서 반복 연습할 수 있습니다. 특히 개인의 지원 자료와 지원 직무를 반영한 질문을 받을 수 있어 일반적인 예상 질문보다 실전 대응력을 높일 수 있습니다.

향후에는 직무별 전문 면접관, 기업별 면접 스타일, 면접 리포트 PDF, 답변 개선 예시, 실시간 발화 습관 분석 등으로 확장할 수 있습니다.

## 참고 문서

- [AI 모의 면접 에이전트 개요](docs/interview-agent-overview.md)
- [Interview Agent 빠른 시작](docs/interview-agent.md)
- [에이전트 구현 계획](docs/interview-agent-plan.md)
- [Upstage API 명세](docs/upstage-api-spec.md)
