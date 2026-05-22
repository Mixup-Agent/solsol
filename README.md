# 쉽약 (SHIPyak) 💊

> 어려운 공약, 쉽게 한 알

**Solar Pro3 기반 공공문서 평이화 멀티에이전트** — 선거 공약집의 행정·법률 용어를 다양한 인구 집단(페르소나)의 언어 수준에 맞춰 자동 변환하는 서비스입니다.

Upstage Solar Pro3 AI Agent 해커톤 출품작.

## 핵심 기능

- 지역 선택 → 후보 공약 즉시 표시 (사전 파싱 DB)
- 페르소나별 이해도 평가 (Agent 3) + 평이화 생성 (Agent 4)
- 원문 항상 병기, 정치적 중립성 구조적 보장

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| 프론트엔드 | React (Vite), Tailwind CSS, Shadcn/UI |
| 백엔드 | FastAPI, LangChain / LangGraph |
| AI | Upstage Solar Pro3 API, Document Parse API, Information Extract API |
| 데이터 | Nemotron-Personas-Korea, SQLite |

## 저장소 구조

```
shipyak/
├── frontend/      # React (Vite) 프론트엔드
├── backend/       # FastAPI 백엔드 + 멀티에이전트
├── data/          # 데이터 수집·전처리·분석
├── design/        # 디자인 에셋, 와이어프레임
├── lovable/       # Lovable 프롬프트 및 생성 코드
├── docs/          # PRD, 협업 가이드, 대회 안내
└── presentation/  # 발표자료, 시연영상
```

## 시작하기

### 1. 저장소 클론

```bash
git clone https://github.com/Mixup-Agent/shipyak.git
cd shipyak
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일에 Upstage API 키 입력
```

### 3. 백엔드 실행

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 4. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

## 협업 가이드

브랜치 전략·작업 규칙은 [docs/team_roles.md](docs/team_roles.md) 를 참고하세요.

## 팀

| 역할 | 담당 영역 | 브랜치 |
|------|----------|--------|
| AI | 에이전트·프롬프트 | `feat/agent` |
| 백엔드 | API·통합 | `feat/backend` |
| 데이터 | 데이터 파이프라인 | `feat/data` |
| 디자인 | UI/UX·발표 | `feat/design` |

## 문서

- [기획서 (PRD)](docs/PRD.md)
- [협업 가이드](docs/team_roles.md)
- [저장소 구조 설계](docs/repo_structure.md)
- [대회 안내](docs/대회_안내.md)
