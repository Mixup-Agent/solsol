# AI 모의 면접 에이전트 시스템

> **같은 이력서를 넣어도, 회사가 다르면 질문이 다릅니다.**
> Solar Pro3의 고유 기능을 역할별로 매핑한 한국형 AI 모의면접 에이전트 시스템

Upstage Solar Pro3 AI Agent 해커톤 출품작입니다. 자소서·이력서·포트폴리오·채용공고를 분석해 그 회사의 실제 면접 스타일을 추론하고, 5개 에이전트가 협력해 동적으로 면접을 진행하는 음성 기반 모의면접 서비스입니다.

## 프로젝트 정보

| 항목 | 내용 |
|------|------|
| 작품명 | AI 모의 면접 에이전트 시스템 |
| 팀명 | 솔솔(solsol) |
| 팀원 | 김나경, 박민영, 유지예, 이정연 |
| 핵심 모델 | Upstage Solar Pro3, Solar Mini |
| 주요 형태 | 웹 기반 음성 모의면접 서비스 |

---

## 🎯 이 프로젝트가 다른 이유

### 1. 회사가 바뀌면 질문이 바뀐다
**메타 에이전트가 회사명과 채용공고를 분석해 그 회사의 실제 면접 스타일을 LLM으로 추론**합니다. 같은 이력서를 넣어도 *토스* 면접과 *삼성전자* 면접은 톤·격식·압박 상한·중점 평가 역량이 달라지고, 모든 면접관 에이전트가 이 프로파일을 공유해 회사 분위기에 맞는 질문을 생성합니다.

| 회사 | 격식 | 압박 상한 | 면접 톤 예시 |
|---|---|:---:|---|
| 토스 (예시) | casual | 2/5 | "가장 임팩트가 컸던 결정의 트레이드오프는?" |
| 삼성전자 (예시) | formal | 4/5 | "MSA 전환 시 데이터 정합성 검증 방법을 단계별로 설명해 주십시오." |

### 2. Solar Pro3의 고유 기능을 역할별로 매핑
*"모델 이름만 박은"* 게 아니라 Pro3의 차별 기능 세 가지를 명시적으로 활용했습니다.

| 역할 | 모델 | reasoning_effort | 목적 |
|---|---|:---:|---|
| 라우터·평가자 (`meta`, `judge`) | Solar Pro3 | **high** | 깊은 판단·종합 평가 |
| 면접관 (`resume`, `trend`, `stress`) | Solar Pro3 | **low** | 빠른 질문 생성 |
| 답변 품질 분류기 (`answer_quality`) | Solar **Mini** | — | 비용·속도 우선 |

추가로 **`prompt_cache_key`로 세션별 캐싱**을 적용해 같은 면접 안에서 이력서·자소서가 매 라운드 반복되는 비용을 줄였습니다.

### 3. 단순 라우터가 아닌 "오케스트레이터 + 가드레일"
메타 에이전트가 LLM 호출 한 번으로 끝나지 않습니다. **3중 가드레일**이 시연 안정성과 면접 흐름의 균형을 보장합니다.

- **답변 품질 게이트** — 답변이 회피적·모순·근거 부족이면 메타가 `stress`로 강제 라우팅
- **trend 하드 캡** — 트렌드 질문이 면접당 최대 2회를 넘지 못하도록 코드 레벨 제한
- **에이전트 균형 보정** — 한 면접관이 다른 면접관보다 2회 이상 앞서면 자동으로 가장 적게 쓰인 면접관으로 보정

### 4. 정적 일반론이 아닌 "실제 뉴스" 기반 트렌드 질문
`trend` 에이전트는 사전 수집한 **네이버 뉴스 DB에서 회사·직무 키워드로 매칭한 실제 기사 본문**을 보고 질문을 만듭니다. 각 질문에 사용된 출처 메타데이터(`current_question_sources`)도 함께 저장해 *"이 질문이 어떤 기사 기반으로 만들어졌는가"* 까지 추적 가능합니다.

---

## 아이디어 배경

최근 면접은 단순한 질문 답변이 아니라 지원자의 경험, 직무 이해도, 문제 해결력, 커뮤니케이션 능력을 종합적으로 평가하는 과정입니다. 더 나아가 회사마다 면접 문화와 평가 기준이 다릅니다. 토스의 임팩트 중심 면접과 삼성의 단계별 검증 면접은 같은 직무라도 요구되는 답변의 결이 완전히 다릅니다.

이 프로젝트는 사용자의 지원 자료와 채용공고를 분석해 **그 회사의 실제 면접 스타일을 추론**하고, 여러 AI 면접관이 역할을 나누어 회사 분위기에 맞는 질문을 이어가는 모의면접 환경을 제공합니다. 면접 종료 후에는 질문과 답변 기록을 바탕으로 강점과 개선점을 정리한 피드백 리포트를 제공합니다.

---

## 핵심 기능

| 기능 | 설명 |
|------|------|
| 지원 자료 입력 | 자소서, 이력서, 포트폴리오 PDF, 회사명, 직무명, 채용공고 링크를 입력합니다. |
| 회사 스타일 추론 | 메타 에이전트가 회사명과 채용공고를 분석해 격식·압박 상한·중점 평가 역량·실제 면접 관행을 추론합니다. |
| 다중 AI 면접관 | 이력서 기반, 뉴스/트렌드 기반, 꼬리질문/압박 질문, 총괄 평가 에이전트가 면접을 진행합니다. |
| 답변 품질 진단 | 매 답변마다 별도 분류기가 score·flag·action_hint를 산출해 메타의 라우팅 결정에 피드백을 제공합니다. |
| 음성 면접 | 사용자의 음성 답변을 STT로 텍스트화하고, 생성된 질문을 TTS 음성으로 출력합니다. |
| 동적 꼬리질문 | 답변의 모호함·근거 부족·구체성 부족을 자동 감지해 압박 면접관으로 강제 라우팅합니다. |
| 최종 피드백 | 전체 대화를 바탕으로 논리성·경험 구체성·트렌드 이해도·종합 점수와 한국어 피드백을 제공합니다. |

---

## 서비스 흐름

```
사용자 입력
  자소서 / 이력서 / 포트폴리오 PDF / 회사명 / 직무명 / 채용공고 URL
        │
        ▼
문서 및 공고 분석
  PDF 파싱, 채용공고 크롤링, 핵심 경험 및 직무 요구사항 추출
        │
        ▼
메타 에이전트 — 회사 스타일 추론 (1회)
  격식 / 압박 상한 / 중점 평가 역량 / 실제 면접 관행 / 대표 질문 패턴
        │
        ▼
AI 모의면접 루프 (라운드 반복)
  Answer Quality → Meta → Resume / Trend / Stress → STT/TTS
        │
        ▼
최종 평가
  Judge 에이전트가 4축 점수와 한국어 피드백 리포트 생성
```

---

## 멀티에이전트 구조

본 시스템은 LangGraph 기반 5개 노드와 1개의 별도 분류기(`answer_quality`)로 구성됩니다.

| Agent | 모델 / reasoning_effort | 책임 |
|-------|---|------|
| `meta` | solar-pro3 / **high** | 회사 스타일 추론 + 동적 라우팅 + 3중 가드레일 |
| `answer_quality` | solar-**mini** | 답변 품질 점수·flag·action_hint 산출 (메타에 피드백) |
| `resume` | solar-pro3 / low | 이력서·자소서 기반 사실 검증 질문 |
| `trend` | solar-pro3 / low | 네이버 뉴스 DB 기반 트렌드 질문 + 출처 추적 |
| `stress` | solar-pro3 / low | 직전 답변 약점 인용 + 컨텍스트 검증 폴백 |
| `judge` | solar-pro3 / **high** | 4축 점수(overall/logic/experience/trend) + 종합 피드백 |

```
              [지원자 답변]
                    │
                    ▼
        ┌─ Answer Quality Classifier (solar-mini)
        │      score / flags / action_hint
        ▼
   ┌──────────────────────────────────────────┐
   │   Meta Orchestrator (solar-pro3 / high)  │
   │   - 회사 스타일 추론 (첫 진입 1회)         │
   │   - quality_gate: 저품질 → stress 강제    │
   │   - trend_cap / balance 가드레일          │
   └─────┬───────────┬──────────┬─────────────┘
         │           │          │
         ▼           ▼          ▼
   [Resume]      [Trend]     [Stress]
   (pro3 low)  (pro3 low +  (pro3 low +
                naver news)  structured)
         │           │          │
         └───────────┼──────────┘
                     ▼
             (max_rounds 도달)
                     │
                     ▼
           [Judge] (solar-pro3 / high)
           overall / logic / experience / trend
```

---

## Upstage Solar Pro3 활용 — 고유 기능을 역할에 매핑

Solar Pro3의 **3가지 고유 기능**과 **Solar Mini와의 분업**으로 *"왜 Solar Pro3여야 하는가"* 에 명확히 답할 수 있게 설계했습니다.

### 기능 × 컴포넌트 매트릭스

| 컴포넌트 | 모델 | reasoning_effort | prompt_cache_key | 이유 |
|---|---|:---:|:---:|---|
| `meta` (라우터·회사 스타일 결정) | solar-pro3 | **high** | ✅ | 다단계 추론·전략적 판단 |
| `judge` (종합 평가) | solar-pro3 | **high** | ✅ | 전체 대화 정밀 평가 |
| `resume` / `trend` / `stress` | solar-pro3 | **low** | ✅ | 질문 1문장 빠른 생성 |
| `answer_quality` (분류기) | solar-**mini** | — | ✅ | 분류 작업은 가볍게 |

### 활용 포인트

| 기능 | 활용 방식 | 효과 |
|---|---|---|
| **`reasoning_effort` 등급 차등** | 깊은 사고가 필요한 라우터·평가자만 high, 질문 생성기는 low | 응답 속도·비용 최적화 |
| **`prompt_cache_key`** | 세션 ID를 캐시 키로 — 이력서·자소서가 매 라운드 반복되는 비용 절감 | 두 번째 라운드부터 캐시 히트 |
| **구조화 출력 (`with_structured_output`)** | `RouteDecision`, `CompanyStyle`, `JudgeResult`, `StressQuestion`, `AnswerQualityResult` 5종 스키마 강제 | JSON 파싱 오류 0 |
| **Solar Mini 분업** | 답변 품질 라벨링(good/fair/bad)은 Mini로 분리 | Pro3 호출 1회 절약 |

### 왜 Solar Pro3여야 하는가
- `reasoning_effort` 파라미터는 Solar Pro3 전용 — 다른 모델에 동일 개념 없음
- 한국어 면접 도메인의 존댓말·관행 표현이 자연스러움
- 한국 기업(토스·네이버·삼성 등)의 실제 면접 후기 정보를 학습 단계에서 풍부하게 보유

---

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| 프론트엔드 | React, Vite, TanStack Router, Tailwind CSS, Radix UI |
| 백엔드 | FastAPI, Python 3.11, Pydantic |
| Agent | LangGraph, LangChain Upstage, Upstage Solar Pro3 / Mini |
| 문서 처리 | pdfplumber, Upstage Document Parse / Information Extract |
| 채용공고 수집 | httpx, BeautifulSoup |
| 트렌드 데이터 | 네이버 뉴스 수집 + SQLite 키워드 매칭 |
| 음성 처리 | OpenAI STT, ElevenLabs TTS, OpenAI TTS fallback |
| 저장소 | Redis(세션), SQLite(인터뷰 기록·뉴스 DB) |

---

## 저장소 구조

```
shipyak/
├── backend/                    # FastAPI 백엔드와 멀티에이전트 로직
│   ├── main.py                 # API 엔트리포인트
│   ├── app/
│   │   ├── agents/             # meta, resume, trend, stress, judge + llm/state/helpers
│   │   ├── routers/            # 세션, 면접, 턴 기록 API
│   │   ├── services/           # answer_quality, naver_news, STT/TTS, 크롤링, 그래프, 저장소
│   │   └── models/             # Pydantic 모델
│   └── scripts/                # 데모 및 데이터 수집 스크립트
├── lovable/                    # 웹 프론트엔드
│   └── src/
│       ├── components/interview/
│       ├── routes/
│       └── assets/interviewers/
├── docs/                       # 설계 문서와 API/에이전트 문서
├── data/                       # 데이터 수집·전처리 자료 + 뉴스 DB
├── design/                     # 디자인 에셋
└── presentation/               # 발표 자료
```

---

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

---

## 주요 API

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/api/v1/session` | 지원 자료 업로드 및 면접 세션 생성 |
| `GET` | `/api/v1/session/{id}` | 세션 조회 |
| `POST` | `/api/v1/session/{id}/start` | 면접 시작 및 첫 질문 생성 (회사 스타일 추론 포함) |
| `POST` | `/api/v1/session/{id}/answer` | 답변 제출 후 다음 질문 생성 |
| `GET` | `/api/v1/session/{id}/report` | 최종 피드백 리포트 조회 |
| `POST` | `/api/interview-sessions/{id}/turns/audio` | 음성 답변 업로드 및 다음 질문 TTS 반환 |
| `GET` | `/health` | 서버 및 Redis 상태 확인 |

---

## 차별점 — 다른 멀티에이전트 데모와의 차이

| 영역 | 일반 멀티에이전트 데모 | 본 프로젝트 |
|---|---|---|
| **회사 적응** | 회사명을 프롬프트에 끼워넣고 끝 | 메타가 채용공고를 분석해 격식·압박 상한·중점 역량·실제 면접 관행을 추론 |
| **라우팅** | 라운드별 고정 순서 (resume → trend → stress 반복) | 답변 품질 분류기(solar-mini)가 매 턴 score·flag·action_hint 산출 → 메타가 동적 선택 |
| **에이전트 견고성** | LLM 응답이 깨지면 시연 멈춤 | 5종 구조화 출력 + 다중 폴백 경로 + 3중 가드레일 (quality_gate, trend_cap, balance) |
| **트렌드 질문** | LLM 학습 시점의 일반론 | 네이버 뉴스 DB에서 키워드 매칭한 실제 기사 + 출처 메타데이터 추적 |
| **Upstage 활용도** | 모델 이름만 박음 | `reasoning_effort` 등급 차등 + `prompt_cache_key` + Mini 분업 |
| **추적 가능성** | 블랙박스 | `meta_decisions`, `answer_quality_history`, `current_question_sources` 세 가지 로그로 *"왜 이 질문이 나왔는가"* 추적 가능 |

### 측정 가능한 결과
- 한 세션당 LLM 호출 패턴: meta(1) + answer_quality(N) + 면접관(N) + judge(1)
- 5종 구조화 스키마로 JSON 파싱 실패율 0
- 데모 영상에서 *"같은 이력서, 회사만 다르게"* 비교 시연 가능

---

## 협업 규칙

- **브랜치 전략** — 팀원별 `feat/*` 브랜치에서 작업 (예: `feat/agent`, `feat/backend`, `feat/data`, `feat/design`). `main`은 항상 동작 가능한 통합 브랜치
- **PR·머지** — `feat/*` → `main` PR 후 머지. 작은 단위로 자주 머지하고, 머지 후 다른 팀원은 `main`을 다시 pull해 동기화
- **커밋** — 작게 자주 push (해커톤 환경 대비 백업). 커밋 메시지는 한국어로, 변경 의도가 한 줄에 드러나게 작성
- **코드 스타일** — PEP 8 준수, snake_case 변수/함수명, 줄 길이 최대 100자. `ruff`로 lint
- **의존성 변경** — 패키지 추가/제거는 반드시 `uv add` / `uv remove`. 변경된 `pyproject.toml`·`uv.lock`을 함께 커밋
- **환경변수** — 모든 API 키는 `.env`로만 관리(하드코딩 금지). `.env.example`만 공유하고 실제 `.env`는 `.gitignore` 처리
- **문서 갱신** — 새 엔드포인트·에이전트·환경변수가 추가되면 README와 `docs/` 관련 문서를 같은 PR에서 갱신

## 기대 효과

취업 준비자는 고비용 면접 컨설팅 없이 실제 면접과 유사한 환경에서 반복 연습할 수 있습니다. 특히 개인의 지원 자료뿐 아니라 **지원 회사의 실제 면접 스타일까지 반영**되기 때문에 일반적인 예상 질문보다 실전 대응력을 높일 수 있습니다.

향후에는 직무별 전문 면접관, 기업별 면접 스타일 라이브러리화, 면접 리포트 PDF, 답변 개선 예시, 실시간 발화 습관 분석 등으로 확장할 수 있습니다.

---

## 참고 문서

- [AI 모의 면접 에이전트 개요](docs/interview-agent-overview.md)
- [에이전트 플로우 상세 문서](docs/02_agent_flow.md)
- [Interview Agent 빠른 시작](docs/interview-agent.md)
- [에이전트 구현 계획](docs/interview-agent-plan.md)
- [Upstage API 명세](docs/upstage-api-spec.md)
- [데모 실행 결과](docs/agent-demo-result.md)
