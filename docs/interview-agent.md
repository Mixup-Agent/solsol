# Interview Agent — 빠른 시작

Solar Pro3 해커톤용 **AI 모의면접 멀티에이전트 시스템** (FastAPI + LangGraph)

이력서·자소서·채용공고를 입력받아, 여러 에이전트가 협력해 맞춤형 면접을 진행하고 평가한다.

---

## 1. 환경 설정

의존성은 [uv](https://docs.astral.sh/uv/)로 관리한다. (uv 미설치 시: `curl -LsSf https://astral.sh/uv/install.sh | sh`)

```bash
cd backend
uv sync          # uv.lock 기준으로 .venv 생성·동기화
```

## 2. API 키 설정

프로젝트 루트의 템플릿을 복사해 `.env`를 만들고 키를 입력한다.

```bash
cp .env.example .env
```

```
ANTHROPIC_API_KEY=sk-ant-xxxxx     # 에이전트 LLM (Claude)
UPSTAGE_API_KEY=up_xxxxx           # Upstage API
```

## 3. Redis 실행

세션 저장소로 Redis를 사용한다. (시스템 서비스 — uv로 설치 불가)

```bash
brew install redis
brew services start redis
```

## 4. 서버 실행

```bash
cd backend
uv run uvicorn main:app --reload
```

- API 문서(Swagger): http://localhost:8000/docs
- 헬스체크: http://localhost:8000/health

---

## 프로젝트 구조

```
shipyak/
├── .env.example                 # 환경변수 템플릿
└── backend/
    ├── main.py                  # FastAPI 엔트리포인트
    ├── pyproject.toml           # 의존성 정의 (uv)
    ├── uv.lock                  # 의존성 잠금 파일 — 커밋 필수
    ├── .python-version          # Python 3.11 고정
    ├── create_mock_pdf.py       # 테스트용 mock PDF 생성 스크립트
    ├── app/
    │   ├── config.py            # 환경설정 (pydantic-settings)
    │   ├── agents/              # LangGraph 노드
    │   │   ├── state.py         # InterviewState (TypedDict)
    │   │   ├── meta.py          # 라우팅·종료 판단
    │   │   ├── resume.py        # 이력서/자소서 기반 질문
    │   │   ├── trend.py         # 최신 트렌드 질문
    │   │   ├── stress.py        # 압박·꼬리 질문
    │   │   └── judge.py         # 전체 평가·피드백
    │   ├── services/
    │   │   ├── graph.py         # LangGraph StateGraph 빌드
    │   │   ├── session_store.py # Redis 세션 저장소
    │   │   ├── crawler.py       # 채용공고 크롤러 (httpx + BS4)
    │   │   └── file_parser.py   # PDF 텍스트 추출 (pdfplumber)
    │   ├── routers/
    │   │   ├── session.py       # 세션 생성/조회/삭제 API
    │   │   └── interview.py     # 면접 시작/답변/리포트 API
    │   ├── models/              # Pydantic 스키마
    │   └── prompts/             # 프롬프트 템플릿 (예정)
    └── scripts/
        └── collect_naver_news.py
```

## 아키텍처

면접 흐름은 LangGraph `StateGraph`로 조립된 멀티에이전트 파이프라인이다.

```
session API → graph(StateGraph) → meta(라우팅) → resume / trend / stress → judge(평가)
```

| 노드 | 역할 | 현재 상태 |
|------|------|----------|
| `meta` | 다음 에이전트 결정·종료 판단 | 스텁 (라운드로빈) |
| `resume` | 이력서·자소서 기반 질문 | 스텁 |
| `trend` | 최신 기술·산업 트렌드 질문 | 스텁 |
| `stress` | 압박·논리 반박·꼬리 질문 | 스텁 |
| `judge` | 전체 면접 평가·피드백 생성 | 스텁 |

- 에이전트 LLM 호출은 `langchain_anthropic.ChatAnthropic`(Claude)로 구현돼 있다.
- 모든 노드는 현재 인라인 프롬프트 **스텁** 상태이며, 프롬프트 고도화가 다음 작업이다.
- 상태 스키마는 `app/agents/state.py`의 `InterviewState`.

## 주요 API

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/session` | 이력서 PDF 업로드 → 세션 생성 |
| GET | `/api/v1/session/{id}` | 세션 조회 |
| POST | `/api/v1/session/{id}/start` | 면접 시작 (첫 질문 생성) |
| POST | `/api/v1/session/{id}/answer` | 답변 제출 → 다음 질문 |
| GET | `/api/v1/session/{id}/report` | 최종 평가 리포트 |

## 의존성 관리

```bash
uv add <패키지>           # 런타임 의존성
uv add --dev <패키지>     # 개발용 의존성
```

추가 후 변경된 `pyproject.toml`·`uv.lock`을 함께 커밋한다.
