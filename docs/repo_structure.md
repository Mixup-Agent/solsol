팀 구성에 맞춰서 레포 구조와 역할 분담을 재설계하겠습니다.

## 팀 구성 분석

| 팀원   | 스킬        | 핵심 강점                   | 약점                 |
| ------ | ----------- | --------------------------- | -------------------- |
| 팀원 A | AI 주력     | LLM 프롬프트, 에이전트 설계 | 프론트 약함          |
| 팀원 B | 백엔드 약간 | API 연결, 간단한 서버       | 복잡한 백엔드는 부담 |
| 팀원 C | 데이터 분석 | 데이터 수집·정제·분석       | 코딩은 보조          |
| 팀원 D | 디자이너    | UI/UX 설계, 비주얼          | 코딩 불가            |

**문제점**: 프론트엔드 개발자가 없음 → **Lovable로 해결**

---

## 재구성된 레포 구조

```
shipyak/
├── README.md
├── .env.example
│
├── lovable/                     # Lovable 생성 코드 (팀원 D 주도)
│   ├── prompts/                 # Lovable에 입력할 프롬프트 모음
│   │   ├── 01_home_page.md      # "홈 화면 생성 프롬프트"
│   │   ├── 02_candidate_select.md
│   │   ├── 03_persona_select.md
│   │   ├── 04_result_view.md
│   │   └── lovable_guide.md     # Lovable 사용 가이드
│   └── generated/               # Lovable가 생성한 코드 저장
│       └── (Lovable 결과물 복붙)
│
├── frontend/                    # 최종 통합 프론트 (팀원 B가 Lovable 코드 통합)
│   ├── src/
│   │   ├── components/          # Lovable 생성 컴포넌트 복사
│   │   ├── pages/
│   │   ├── services/
│   │   │   └── api.js           # ← 팀원 B가 백엔드 연결
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── backend/                     # 팀원 B 주도
│   ├── app/
│   │   ├── main.py              # FastAPI 엔트리포인트
│   │   ├── config.py
│   │   ├── routers/
│   │   │   ├── pledge.py        # 공약 조회 API
│   │   │   ├── persona.py       # 페르소나 API
│   │   │   └── simplify.py      # 평이화 실행 API
│   │   ├── agents/
│   │   │   ├── orchestrator.py  # 팀원 A와 협업
│   │   │   ├── readability.py   # Agent 3 (팀원 A)
│   │   │   └── simplifier.py    # Agent 4 (팀원 A)
│   │   ├── services/
│   │   │   └── upstage_client.py # Upstage API 래퍼
│   │   └── prompts/
│   │       ├── readability.txt   # ← 팀원 A가 작성
│   │       └── simplify.txt      # ← 팀원 A가 작성
│   ├── requirements.txt
│   └── test_api.py              # 간단한 테스트
│
├── data/                        # 팀원 C 주도
│   ├── collection/              # 데이터 수집 스크립트
│   │   ├── download_pdfs.py     # 선관위에서 PDF 다운
│   │   ├── scrape_nec.py        # 선관위 웹 크롤링 (필요시)
│   │   └── collection_log.md
│   ├── preprocessing/           # 전처리 스크립트
│   │   ├── preparse_batch.py    # Agent 1·2 배치 실행
│   │   ├── validate_data.py     # 데이터 검증
│   │   └── nemotron_loader.py   # Nemotron 페르소나 로드
│   ├── raw/                     # 원본 데이터
│   │   ├── pdfs/
│   │   │   └── 2022_pledges/
│   │   └── nemotron/
│   │       └── personas_sample.json
│   ├── processed/               # 가공된 데이터
│   │   ├── pledges_db.json      # 사전 파싱 결과
│   │   └── personas_final.json
│   ├── analysis/                # 데이터 분석 (팀원 C)
│   │   ├── readability_stats.ipynb  # 가독성 점수 분석
│   │   └── persona_coverage.ipynb   # 페르소나 커버리지
│   └── rules/
│       ├── easy_language_guide.pdf
│       └── vocab_levels.csv
│
├── design/                      # 팀원 D 주도
│   ├── figma/
│   │   └── shipyak_wireframes.fig
│   ├── wireframes/              # 와이어프레임 이미지
│   │   ├── 01_home.png
│   │   ├── 02_candidate_select.png
│   │   ├── 03_persona_select.png
│   │   └── 04_result.png
│   ├── assets/
│   │   ├── logo.svg
│   │   ├── icon_pill.svg
│   │   └── colors.md            # 컬러 팔레트
│   └── style_guide.md           # 디자인 가이드
│
├── docs/
│   ├── PRD.md
│   ├── team_roles.md            # 팀 역할 분담
│   ├── setup_guide.md           # 개발 환경 세팅
│   └── demo_script.md           # 시연 대본
│
└── presentation/
    ├── ppt/
    │   └── shipyak_final.pptx   # 팀원 D가 디자인
    └── video/
        └── demo_script.md
```

---

## 역할별 상세 분담

### 팀원 A (AI 주력) — Agent 품질 책임자

**핵심 업무**:

- Agent 3·4의 시스템 프롬프트 작성 및 튜닝 (가장 중요!)
- Upstage Solar Pro3 API 테스트 및 파라미터 조정
- 평이화 품질 검증 (출력 샘플 리뷰)

**담당 파일**:

```
backend/
  └── prompts/
      ├── system_readability.txt    # Agent 3 프롬프트
      ├── system_simplify.txt       # Agent 4 프롬프트
      ├── plain_language_rules.txt  # 쉬운 말 규칙
      └── forbidden_patterns.txt    # 금지 패턴

backend/agents/
  ├── readability.py    # Agent 3 로직 (팀원 B와 협업)
  └── simplifier.py     # Agent 4 로직 (팀원 B와 협업)
```

**Lovable 활용**:

- 프롬프트 테스트용 간단한 UI를 Lovable로 생성 가능
- "Agent 3 테스트 화면: 텍스트 입력 → 이해도 점수 출력"

**타임라인**:

- T+0~2: Upstage API 테스트 + 초기 프롬프트 작성
- T+2~6: 프롬프트 반복 튜닝 (샘플 10개로 테스트)
- T+6~10: 팀원 B와 협업하여 오케스트레이터 통합
- T+10~12: 최종 품질 검증 (시연 케이스 3개)

---

### 팀원 B (백엔드 약간) — 통합 담당자

**핵심 업무**:

- FastAPI 서버 세팅 및 API 엔드포인트 생성
- Lovable 생성 프론트엔드와 백엔드 연결
- Upstage API 클라이언트 래퍼 작성

**담당 파일**:

```
backend/
  ├── main.py           # FastAPI 앱
  ├── routers/          # API 엔드포인트
  └── services/
      └── upstage_client.py  # Upstage API 래퍼

frontend/
  └── src/services/
      └── api.js        # 프론트 → 백엔드 호출
```

**Lovable 활용**:

- Lovable이 생성한 React 컴포넌트를 `frontend/src/`에 복사
- `api.js`만 직접 작성해서 백엔드 연결

**타임라인**:

- T+0~2: FastAPI 세팅 + Upstage API 테스트
- T+2~4: `/api/simplify` 엔드포인트 생성 (Agent 3·4 호출)
- T+4~6: Lovable 코드 통합 + `api.js` 작성
- T+6~10: 팀원 A의 Agent와 연결 테스트
- T+10~12: 버그 수정

---

### 팀원 C (데이터 분석) — 데이터 파이프라인 책임자

**핵심 업무**:

- 2022년 공약 PDF 10~15건 다운로드
- Agent 1·2로 사전 파싱 (배치 스크립트 작성)
- Nemotron 페르소나 데이터 로드 및 샘플 4명 추출
- 데이터 품질 검증 (파싱 결과가 올바른지 확인)

**담당 파일**:

```
data/
  ├── collection/
  │   ├── download_pdfs.py      # PDF 다운로드 스크립트
  │   └── scrape_nec.py         # 크롤링 (필요시)
  ├── preprocessing/
  │   ├── preparse_batch.py     # Agent 1·2 배치 실행
  │   └── nemotron_loader.py    # 페르소나 로드
  └── analysis/
      ├── readability_stats.ipynb
      └── persona_coverage.ipynb
```

**Lovable 활용**:

- 데이터 분석 결과를 시각화할 대시보드를 Lovable로 생성 가능
- "공약 분야별 난이도 통계 차트" 같은 간단한 대시보드

**타임라인**:

- T+0~1: 선관위 사이트에서 2022년 PDF 10건 다운로드
- T+1~2: `preparse_batch.py` 작성 + Agent 1·2 실행
- T+2~4: 파싱 결과 검증 (JSON 형식 확인, 누락 체크)
- T+4~6: Nemotron 데이터 로드 + 페르소나 4명 추출
- T+6~8: 데이터 분석 (가독성 통계, 어려운 단어 빈도)
- T+8~12: 시연 케이스 데이터 최종 준비

---

### 팀원 D (디자이너) — UI/UX 및 발표 자료 책임자

**핵심 업무**:

- Figma에서 와이어프레임 설계
- Lovable에 프롬프트 입력하여 UI 컴포넌트 생성
- PPT 디자인 (시연 영상 포함)
- 로고, 아이콘, 컬러 팔레트 제작

**담당 파일**:

```
design/
  ├── figma/
  │   └── shipyak_wireframes.fig
  ├── wireframes/
  ├── assets/
  │   ├── logo.svg
  │   └── colors.md
  └── style_guide.md

lovable/
  ├── prompts/
  │   ├── 01_home_page.md       # Lovable 프롬프트
  │   ├── 02_candidate_select.md
  │   └── ...
  └── generated/

presentation/
  └── ppt/
      └── shipyak_final.pptx
```

**Lovable 활용 전략** (가장 중요!):

#### Step 1: Figma에서 와이어프레임 완성 (T+0~2)

- PRD의 와이어프레임을 Figma로 디자인
- 컬러, 폰트, 간격 확정

#### Step 2: Lovable 프롬프트 작성 (T+2~4)

**예시: 홈 화면 프롬프트**

```markdown
# Lovable 프롬프트: 홈 화면

다음 요구사항을 만족하는 React 컴포넌트를 생성해줘:

## 디자인 요구사항

- 컬러: 메인 파란색 #3B82F6, 배경 흰색
- 폰트: Pretendard (없으면 Inter)
- 모바일 우선 반응형

## 레이아웃

- 상단: 로고 "쉽약 💊" + "어려운 공약, 쉽게 한 알"
- 중간: 현재 위치 표시 "📍 경기 성남시 분당구" + [변경] 버튼
- 메인 버튼: "우리 동네 후보 공약 보기" (크고 파란색)
- 하단: "⚖️ 모든 후보를 동일 기준으로 풀어씁니다"
- 맨 아래: "📄 공약 PDF 직접 올리기 →" (작은 링크)

## 컴포넌트 구조

- HomePage.jsx
- HeroSection.jsx (상단)
- LocationDetector.jsx (위치 감지)
- MainCTA.jsx (메인 버튼)

Tailwind CSS 사용, Shadcn/UI 컴포넌트 활용
```

#### Step 3: Lovable 실행 → 코드 생성 (T+4~6)

- Lovable에 프롬프트 입력
- 생성된 코드를 `lovable/generated/`에 저장
- 팀원 B에게 전달

#### Step 4: 수정 요청 반복 (T+6~8)

- 생성된 UI를 보고 Lovable에 "버튼 크기를 더 크게", "여백 조정" 등 수정 요청
- 최종 컴포넌트를 `frontend/src/`로 복사

**타임라인**:

- T+0~2: Figma 와이어프레임 완성
- T+2~4: Lovable 프롬프트 4개 작성 (홈/후보/페르소나/결과)
- T+4~6: Lovable로 컴포넌트 생성 (4개 화면)
- T+6~8: 생성된 코드 검수 + 수정 요청
- T+8~10: 팀원 B와 협업 (통합 지원)
- T+10~12: PPT 디자인
- T+12~14: 시연 영상 제작 지원

---

## Lovable 활용 전략 상세

### Lovable 크레딧 100을 어떻게 쓸까?

각 팀원이 100 크레딧씩 있으므로 총 400 크레딧. 1개 화면 생성 ≈ 10~20 크레딧 소모 예상.

| 팀원   | Lovable 용도                               | 예상 크레딧 소모 |
| ------ | ------------------------------------------ | ---------------- |
| 팀원 D | 메인 4개 화면 생성 (홈/후보/페르소나/결과) | 60~80            |
| 팀원 D | 수정 요청 반복 (디테일 조정)               | 20               |
| 팀원 A | Agent 테스트 UI 생성                       | 10               |
| 팀원 C | 데이터 분석 대시보드                       | 10               |
| 여유분 | 버그 수정, 추가 기능                       | 20               |

### Lovable 프롬프트 예시 모음

**1. 후보 선택 화면**

```
React 컴포넌트를 만들어줘:
- 상단: 탭 3개 [시도지사] [구시군의장] [교육감]
- 카드 3개: 기호 1·2·3번 후보
- 각 카드: 후보명 + 정당 + 공약 3줄 미리보기 + "공약 풀어보기 →" 버튼
- Tailwind, 모바일 반응형
```

**2. 페르소나 선택 화면**

```
React 컴포넌트:
- 제목: "누구의 눈높이로 볼까요?"
- 그리드 2x2: 4개 카드
  - 카드 1: 이모지 👵 + "70대 어르신" + 서브텍스트 "큰 글씨, 쉬운 말"
  - 카드 2: 👩‍💼 + "30대 직장인" + "빠르게, 핵심만"
  - 카드 3: 🧑‍🍳 + "50대 자영업자" + "세금·지원금 중심"
  - 카드 4: 🌏 + "외국인 주민" + "쉬운 한국어"
- 하단: "✏️ 직접 입력하기" 버튼
- Tailwind, hover 효과
```

**3. 결과 화면 (가장 복잡)**

```
React 컴포넌트:
- 상단: 후보 이름 + 선택된 페르소나 표시
- 탭 2개: [📄 원문] [💬 쉬운말]
- 원문 탭:
  - 공약 원문 텍스트
  - 어려운 단어 하이라이트 (노란색 배경)
  - 이해도 뱃지: ❌ 어려움
  - "쉬운말로 보기 →" 버튼
- 쉬운말 탭:
  - 원문 (회색 박스)
  - ↓ 화살표
  - 평이화 텍스트
  - "바뀐 단어:" 표시
  - ✅ 이해도: 쉬움
  - 하단: 📤 공유 버튼 + 👍👎 피드백
- 맨 아래: ⚠️ 면책 고지 (회색 박스)
```

---

## 24시간 타임라인 (팀 스킬 반영)

| 시간    | 팀원 A (AI)                | 팀원 B (백엔드)            | 팀원 C (데이터)         | 팀원 D (디자인)           |
| ------- | -------------------------- | -------------------------- | ----------------------- | ------------------------- |
| T+0~1   | Upstage API 테스트         | FastAPI 세팅               | PDF 10건 다운로드       | Figma 와이어프레임        |
| T+1~2   | 프롬프트 초안 작성         | Upstage 래퍼 작성          | **사전 파싱 배치 실행** | Lovable 프롬프트 작성     |
| T+2~4   | Agent 3 개발 + 테스트      | `/api/simplify` 엔드포인트 | 파싱 결과 검증          | Lovable로 홈 화면 생성    |
| T+4~6   | Agent 4 개발 + 재검증 루프 | Agent 3·4 통합             | Nemotron 페르소나 로드  | Lovable로 나머지 3개 화면 |
| T+6~8   | 프롬프트 튜닝 (품질 개선)  | 프론트 연결 (`api.js`)     | 데이터 분석 (통계)      | 생성 코드 검수 + 수정     |
| T+8~10  | 시연 케이스 품질 검증      | 통합 테스트 + 버그 수정    | 시연 케이스 데이터 준비 | 팀원 B 통합 지원          |
| T+10~12 | 최종 품질 확인             | 최종 테스트                | 백업 데이터 준비        | PPT 디자인                |
| T+12~14 | 발표 리허설                | GitHub 정리                | 데이터 문서화           | 시연 영상 제작            |

---

## 핵심 성공 포인트

### 1. 팀원 D가 Lovable을 잘 쓰는 게 핵심

- 프론트엔드 개발자 없이 UI를 완성하는 유일한 방법
- 좋은 프롬프트 = 좋은 UI
- **사전 준비**: Lovable 튜토리얼 1시간 미리 보기

### 2. 팀원 C가 T+1~2에 사전 파싱 완료

- 이후 전 팀원이 파싱된 데이터로 개발 가능
- 가장 중요한 마일스톤

### 3. 팀원 A의 프롬프트 품질 = 서비스 품질

- Agent 3·4의 프롬프트를 T+2~6에 집중적으로 튜닝
- 샘플 10개로 반복 테스트

### 4. 팀원 B는 "접착제" 역할

- Lovable 코드 + 백엔드 + Agent를 모두 연결
- 가장 바쁜 팀원이므로 다른 팀원이 적극 지원

---

이 구조로 가면 **프론트엔드 개발자 없이도 완성도 높은 MVP**를 만들 수 있습니다. Lovable이 핵심 전력입니다!
