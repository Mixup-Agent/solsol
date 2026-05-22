# AI 모의 면접 에이전트 시스템 - 프로젝트 개요

> ⚠️ **이 문서는 초기 설계 문서(설계 비전)입니다.**
> 실제 구현 구조·실행 방법은 [interview-agent.md](./interview-agent.md)를 기준으로 하세요.
> 현재 코드에는 5개 LangGraph 노드(`meta`·`resume`·`trend`·`stress`·`judge`)만 구현돼 있으며,
> 아래 10개 에이전트 구성은 달성 목표 설계입니다.

## 📋 프로젝트 정보

**대회**: Solar Pro3 AI Agent 해커톤  
**팀 구성**: 4명 (민영, 나경, 정연, 4번)  
**개발 기간**: 무박 2일 (2025년 5월 22~23일)  
**목표**: Solar Pro3 기반 Multi-Agent 면접 시스템 구현 및 시연

---

## 🎯 핵심 컨셉

### 문제 정의
취업 준비생들은 면접 준비를 위해 고비용의 1:1 컨설팅(회당 5~15만원)을 받거나, 일반적인 질문만 제공하는 단순 챗봇에 의존하고 있음. **개인화되고 동적으로 적응하는** 면접 연습 솔루션이 필요.

### 차별화 포인트: "왜 Agent여야 하는가"

1. **동적 계획**: 이력서·JD·기업 컨텍스트를 분석해 맞춤형 질문 전략 수립
2. **도구 사용**: 실시간 웹 검색으로 최신 기업 뉴스 반영
3. **상태 추적**: 답변 누적 분석, 강약점 가설 업데이트, 적응적 follow-up
4. **자기 검토**: 질문 난이도·편향을 평가하고 조정

> **단순 챗봇과의 차이**: GPT에게 "면접 봐줘"라고 하면 정적인 질문만 받지만, 이 시스템은 **계획→실행→평가→조정** 전체 루프를 자동 수행

---

## 🏗️ 시스템 아키텍처

### 전체 구조 (4단계 파이프라인)

```
[1단계: 문서 처리]  →  [2단계: 분석·계획]  →  [3단계: 음성 면접 루프]  →  [4단계: 보고서]
    Document              Interview              Voice Interview             Coach
    Processor             Planner                + 3 Agents                  Agent
    + Research            Agent                  (Orchestrator 제어)
```

### Multi-Agent 구성

#### 1️⃣ **Document Processor Agent** (민영 담당)
**역할**: 입력 문서 파싱 및 구조화
- **Input**: 자소서 PDF, 이력서 PDF, 포트폴리오 PDF
- **Tools**: 
  - Upstage Document Parse API
  - Upstage Information Extract API
- **Output**: 
  ```json
  {
    "profile": {
      "education": [...],
      "experience": [...],
      "projects": [...],
      "skills": [...]
    },
    "cover_letter_summary": "핵심 동기 3줄",
    "portfolio_highlights": [...]
  }
  ```

#### 2️⃣ **Company Research Agent** (민영 담당)
**역할**: 기업·직무·채용공고 정보 수집
- **Input**: 회사명, 직무명, 채용공고 URL
- **Tools**:
  - web_search (최근 뉴스, IR 자료)
  - web_fetch + BeautifulSoup (JD 스크래핑)
  - Solar Pro3 (핵심 요구사항 정제)
- **Output**:
  ```json
  {
    "company_context": {
      "recent_news": [...],
      "culture_keywords": [...],
      "tech_stack": [...]
    },
    "jd_requirements": {
      "must_have": [...],
      "nice_to_have": [...]
    }
  }
  ```

#### 3️⃣ **Interview Planner Agent** (정연 담당)
**역할**: 프로필 vs JD gap 분석 및 질문 전략 수립
- **Input**: profile + company_context + jd_requirements
- **Tools**:
  - Upstage Embeddings (이력서↔JD 유사도)
  - Solar Pro3 (gap 분석, 질문 우선순위)
- **Output**:
  ```json
  {
    "question_strategy": [
      {
        "category": "기술 검증",
        "priority": 1,
        "base_question": "...",
        "follow_ups": {
          "if_weak": "...",
          "if_strong": "..."
        }
      }
    ],
    "estimated_duration": "20분",
    "question_count": 8
  }
  ```

#### 4️⃣ **Resume Agent** (정연 담당)
**역할**: 이력서 기반 사실 검증 질문
- **특징**: 구체성 파고들기, STAR 프레임워크 완성 유도
- **프롬프트 핵심**:
  - "모호한 답변에는 '구체적으로 어떻게?'"
  - "경험 중 가장 검증 필요한 부분 선택"
  - "수치, 사례, 의사결정 과정 요구"

#### 5️⃣ **Stress Agent** (정연 담당)
**역할**: 압박 질문 및 논리 검증
- **특징**: 직전 답변의 약점 공략, 반박, 지속 질문
- **프롬프트 핵심**:
  - "답변에서 약점, 모순, 모호함 찾기"
  - "적당히 의심하는 톤"
  - "다른 선택지는? 실패 가능성은?"

#### 6️⃣ **Trend Agent** (정연 담당 - 선택)
**역할**: 최신 산업/기술 트렌드 기반 질문
- **특징**: RAG (뉴스, 기술 블로그 검색)
- **프롬프트 핵심**:
  - "최신 기술 트렌드가 지원자 도메인에 미칠 영향"
  - "업계 이슈에 대한 의견"

#### 7️⃣ **Meta Interview Agent** (나경 담당)
**역할**: 전체 면접 흐름 제어 (오케스트레이터)
- **기능**:
  1. 다음 에이전트 선택 (Resume/Stress/Trend)
  2. 난이도 조절 (답변 품질 기반)
  3. 질문 순서 결정
  4. 종료 조건 판단 (8개 질문 또는 20분)
- **State 관리**:
  ```python
  {
    "current_question_index": 0,
    "asked_questions": [],
    "answers_history": [],
    "evaluation_scores": {},
    "should_follow_up": False,
    "remaining_time": 1200
  }
  ```

#### 8️⃣ **Evaluator Agent** (정연/나경 협업)
**역할**: 답변 실시간 평가
- **평가 차원**:
  - technical_depth (1~5)
  - star_framework (S/T/A/R 완성도)
  - consistency (자소서·이력서 일치도)
  - communication (논리성, 간결성)
  - red_flags (모호함, 과장, 회피)
- **Output**: 점수 + follow-up 필요 여부 판단

#### 9️⃣ **Voice Interface Agent** (4번 담당)
**역할**: 음성↔텍스트 양방향 변환
- **Tools**:
  - STT: OpenAI Whisper API (한국어 정확도)
  - TTS: ElevenLabs 또는 Google Cloud TTS
- **구현 방식**: 턴제 (MVP), 실시간 스트리밍 (stretch goal)

#### 🔟 **Coach Agent** (민영 담당)
**역할**: 최종 피드백 보고서 생성
- **Input**: 전체 면접 transcript + 평가 점수
- **Tools**: Solar Pro3 (종합 분석), ReportLab/FPDF (PDF)
- **Output**: 
  - 전체 점수 요약 (레이더 차트)
  - 강점 TOP 3
  - 약점 & 개선 방향
  - 후속 예상 질문 5개
  - 답변 개선 예시 (Before/After)

---

## 🛠️ 기술 스택

### Upstage API 활용 (25점 배점)

| API | 사용 목적 | 담당 에이전트 |
|-----|----------|-------------|
| **Document Parse** | 이력서/자소서 PDF 파싱 (표·섹션 구조 보존) | Document Processor |
| **Information Extract** | 학력·경력·프로젝트·스킬 구조화 | Document Processor |
| **Solar Pro3** | 모든 reasoning (질문 생성, 평가, 오케스트레이션) | 전 에이전트 |
| **Embeddings** | 이력서↔JD 매칭, 유사 질문 retrieval | Interview Planner |

### 외부 API

| API | 용도 | 우선순위 |
|-----|------|---------|
| **web_search** | 기업 뉴스, 최신 정보 | 필수 |
| **web_fetch** | 채용공고 스크래핑 | 필수 |
| **OpenAI Whisper** | STT (음성→텍스트) | 필수 |
| **ElevenLabs / Google TTS** | TTS (텍스트→음성) | 필수 |
| **BeautifulSoup** | HTML 파싱 | 필수 |
| **ReportLab / FPDF** | PDF 보고서 생성 | 필수 |

### 백엔드 프레임워크

- **FastAPI**: REST API 서버
- **Python 3.10+**: 기본 언어
- **SQLite** (선택): 세션 상태 저장

---

## 📂 프로젝트 구조

> 아래는 **현재 구현 기준** 구조입니다. 상세는 [interview-agent.md](./interview-agent.md) 참고.

```
backend/
├── main.py                  # FastAPI 엔트리포인트
├── pyproject.toml / uv.lock # 의존성 (uv)
├── app/
│   ├── config.py            # 환경설정 (pydantic-settings)
│   ├── agents/              # LangGraph 노드: state, meta, resume, trend, stress, judge
│   ├── services/            # graph(StateGraph), session_store(Redis), crawler, file_parser
│   ├── routers/             # session, interview API
│   ├── models/              # Pydantic 스키마
│   └── prompts/             # 프롬프트 템플릿 (예정)
└── scripts/                 # 데이터 수집 스크립트
```

---

## 🔄 데이터 흐름

### 1. 입력 단계
```
사용자 → 프론트엔드
  ↓
- 자소서 PDF
- 이력서 PDF
- 포트폴리오 PDF
- 회사명
- 직무명
- 채용공고 URL
  ↓
POST /interview/start
```

### 2. 전처리 단계
```
Document Processor → Upstage Document Parse
  ↓
구조화된 profile JSON
  ↓
Company Research → web_search + web_fetch
  ↓
company_context + jd_requirements
  ↓
Interview Planner → Embeddings + Solar Pro3
  ↓
question_strategy (질문 트리)
```

### 3. 면접 루프
```
Meta Agent: decide_next_action()
  ↓
Resume/Stress/Trend Agent 호출
  ↓
질문 생성 (Solar Pro3)
  ↓
TTS → 음성 출력
  ↓
사용자 답변 (음성)
  ↓
STT → 텍스트 변환
  ↓
Evaluator: 답변 평가
  ↓
Meta Agent: 다음 에이전트 결정
  ↓
반복 (8회 또는 20분)
```

### 4. 출력 단계
```
Coach Agent
  ↓
전체 transcript + 평가 점수 종합
  ↓
Solar Pro3로 피드백 생성
  ↓
ReportLab으로 PDF 생성
  ↓
GET /interview/report
  ↓
사용자 다운로드
```

---

## 📡 API 명세 (백엔드)

### POST /interview/start
**Request**:
```json
{
  "resume_pdf": "base64_encoded_pdf",
  "cover_letter_pdf": "base64_encoded_pdf",
  "portfolio_pdf": "base64_encoded_pdf",
  "company_name": "테크 스타트업 B",
  "position": "백엔드 개발자",
  "job_posting_url": "https://..."
}
```

**Response**:
```json
{
  "session_id": "uuid-xxx",
  "status": "processing",
  "estimated_time": "2분"
}
```

### GET /interview/status/{session_id}
**Response**:
```json
{
  "status": "ready",
  "profile_summary": {...},
  "question_count": 8
}
```

### POST /interview/answer
**Request**:
```json
{
  "session_id": "uuid-xxx",
  "answer_audio": "base64_encoded_audio",
  "answer_text": "..." // STT 결과 (optional)
}
```

**Response**:
```json
{
  "next_question": {
    "text": "MSA 전환 시 service boundary를...",
    "audio": "base64_encoded_audio",
    "agent_type": "stress",
    "question_number": 3
  },
  "evaluation": {
    "score": 3.5,
    "feedback": "구체성 부족, Result 누락"
  },
  "is_finished": false
}
```

### POST /interview/end
**Request**:
```json
{
  "session_id": "uuid-xxx"
}
```

**Response**:
```json
{
  "report_url": "/reports/uuid-xxx.pdf",
  "overall_score": 3.8,
  "strengths": [...],
  "weaknesses": [...]
}
```

### GET /reports/{session_id}.pdf
**Response**: PDF 파일 다운로드

---

## 🎯 개발 우선순위 & 타임라인

### Day 1 오전 (4시간)
**목표**: 핵심 에이전트 3개 동작 + 텍스트 기반 1회 면접 성공

| 시간 | 담당 | 작업 |
|------|------|------|
| 10:00-11:00 | 전원 | API 키 발급, 환경 설정, repo 구조 확정 |
| 11:00-13:00 | 민영 | Document Parse + Research 완료 |
| 11:00-13:00 | 나경 | FastAPI 기본 구조 + `/start` 엔드포인트 |
| 11:00-13:00 | 정연 | Resume Agent + 프롬프트 v1 |
| 11:00-13:00 | 4번 | Streamlit 기본 UI (텍스트 입력) |

### Day 1 오후 (4시간)
**목표**: 통합 1차, 텍스트 면접 E2E

| 시간 | 담당 | 작업 |
|------|------|------|
| 14:00-16:00 | 정연 | Stress Agent + Meta Agent 기본 로직 |
| 14:00-16:00 | 나경 | `/answer` 엔드포인트 + state 관리 |
| 14:00-16:00 | 민영 | JD 스크래핑 완료, 데이터 구조 확정 |
| 14:00-16:00 | 4번 | 백엔드 API 연동 |
| 16:00-18:00 | 전원 | **통합 테스트: 텍스트 8개 질문 E2E** |

### Day 1 저녁 (4시간)
**목표**: 프롬프트 튜닝 + 시연 시나리오 준비

| 시간 | 작업 |
|------|------|
| 19:00-20:00 | 정연: 질문 품질 개선, 시연 시나리오 3개 작성 |
| 19:00-20:00 | 민영: 보고서 PDF 템플릿 설계 |
| 20:00-22:00 | 전원: 시연 리허설, 버그 수정 |

### Day 2 새벽 (선택, 3시간)
| 시간 | 작업 |
|------|------|
| 00:00-03:00 | 정연: Trend Agent + RAG (시간 남으면) |
| 00:00-03:00 | 4번: STT/TTS 통합 시도 |

### Day 2 오전 (3시간)
**목표**: 음성 통합 + 보고서 완성

| 시간 | 담당 | 작업 |
|------|------|------|
| 09:00-12:00 | 4번 | STT/TTS 통합 완료, 음성 루프 1회 성공 |
| 09:00-12:00 | 민영 | PDF 보고서 생성 완료 |
| 09:00-12:00 | 나경 | 에러 처리, 로깅, 안정화 |
| 09:00-12:00 | 정연 | 프롬프트 최종 튜닝 |

### Day 2 오후 (3시간)
**목표**: 시연 준비

| 시간 | 작업 |
|------|------|
| 13:00-14:00 | 라이브 데모 리허설 3회 |
| 14:00-15:00 | 백업 영상 녹화, 발표 자료 마무리 |
| 15:00-16:00 | 최종 점검 |

---

## ✅ Critical Path (이거 막히면 끝)

1. **Day 1 오후 6시**: 텍스트 기반 1회 면접 완료 (필수)
   - 이게 안 되면 음성·보고서 의미 없음
   
2. **Day 1 밤 10시**: Resume + Stress 질문 품질 OK
   - 질문이 허접하면 기술 좋아도 탈락

3. **Day 2 오전 12시**: 음성 OR 보고서 둘 중 하나 완성
   - 둘 다 실패 시 "구현 완성도" 점수 폭삭

---

## 🔧 구현 메모

- 에이전트 LLM 호출은 `langchain_anthropic.ChatAnthropic`(Claude)로 구현돼 있다.
- 면접 흐름은 LangGraph `StateGraph`로 조립된다 (`app/services/graph.py`).
- 실제 코드 구조·실행 방법은 [interview-agent.md](./interview-agent.md)를 참고할 것.