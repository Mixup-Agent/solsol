# 🌙 밤샘 개발 플랜 - 내일 아침 8시 제출

## ⏰ 현재 시각 기준 타임라인 (12시간)

**목표**: 동작하는 MVP + 제출물 4개 완성

---

## 🎯 제출 필수 항목

| 제출물 | 담당 제안 | 마감 시각 |
|--------|----------|----------|
| ① 기획서 PDF | 전원 협업 | 새벽 5시 |
| ② GitHub 링크 | 나경 (repo 정리) | 새벽 6시 |
| ③ 발표자료 PPT | 정연 | 새벽 6시 |
| ④ 시연영상 (유튜브) | 4번 | 새벽 7시 |

---

## 🔥 절대 우선순위 (이것만 되면 제출 가능)

### MVP 최소 범위

**MUST HAVE** (없으면 0점):
1. ✅ 이력서 1개 파싱 성공 (Document Parse)
2. ✅ Resume Agent가 질문 3개 생성
3. ✅ 텍스트 기반 Q&A 1회 완료 (음성 NO)
4. ✅ 답변 평가 점수 출력
5. ✅ 간단한 피드백 텍스트 (PDF 아님, 그냥 텍스트)
6. ✅ GitHub에 코드 올라가 있음
7. ✅ 2분 시연 영상 (화면 녹화)

**NICE TO HAVE** (있으면 가산점):
- 음성 STT/TTS ❌ **포기**
- Trend Agent ❌ **포기**  
- PDF 보고서 ❌ **일단 포기, 시간 남으면**
- 백엔드 API ❌ **포기, 단일 스크립트로**

---

## ⏱️ 시간별 작업 계획

### 🕐 지금 ~ 밤 10시 (3시간) - 핵심 에이전트 완성

**정연 (에이전트 담당)**
- [ ] Resume Agent 완성 + 테스트 (질문 5개 생성 확인)
- [ ] Stress Agent 완성 (1개만 만들고 통합)
- [ ] Meta Agent 기본 로직 (순서 정하기만)
- [ ] 시연용 시나리오 1개 작성

**민영 (데이터)**
- [ ] 샘플 이력서 1개 Document Parse로 파싱
- [ ] profile JSON 구조 확정 → 팀 공유
- [ ] 간단한 텍스트 피드백 생성 함수 (Solar로 요약만)

**나경 (백엔드) → 역할 변경**
- [ ] ❌ FastAPI 포기
- [ ] ✅ 단일 Python 스크립트로 전체 흐름 통합
- [ ] `main.py`: 데이터 로드 → 질문 생성 → 답변 입력 → 평가 → 피드백

**4번 (UI) → 역할 변경**
- [ ] ❌ 음성 포기
- [ ] ✅ Streamlit 간단 UI만
- [ ] 텍스트 입력칸 + 질문 출력 + 답변 입력 → 다음 질문

---

### 🕙 밤 10시 ~ 새벽 2시 (4시간) - 통합 & 시연 준비

**전원 협업**
- [ ] 통합 스크립트 1회 E2E 실행 (밤 11시까지 필수)
- [ ] 버그 수정
- [ ] 시연 시나리오로 3회 실행 → 결과 스크린샷

**정연**
- [ ] 발표 자료 PPT 작성 시작
  - 슬라이드 1: 문제 정의
  - 슬라이드 2: 솔루션 (Multi-Agent 구조도)
  - 슬라이드 3: 기술 스택 (Upstage API 강조)
  - 슬라이드 4: 시연 (스크린샷 캡쳐)
  - 슬라이드 5: 비즈니스 임팩트

**나경**
- [ ] GitHub repo 정리
  - README.md 작성
  - 코드 주석 추가
  - requirements.txt 확인
  - .env.example 포함

---

### 🕑 새벽 2시 ~ 5시 (3시간) - 기획서 & 발표자료

**기획서 작성** (전원 협업)
- [ ] HWP 양식 다운로드
- [ ] 섹션별 분담:
  - 문제 정의 & 솔루션: 정연
  - 기술 구현: 나경
  - 데이터 & 결과: 민영
  - 향후 계획: 4번
- [ ] PDF 변환 (새벽 5시)

**발표자료 완성** (정연)
- [ ] PPT 최종본 (새벽 5시)

---

### 🕕 새벽 5시 ~ 7시 (2시간) - 시연 영상 녹화

**4번**
- [ ] OBS 또는 화면 녹화 프로그램 설정
- [ ] 시연 시나리오 리허설 2회
- [ ] 녹화 (2~3분):
  1. 이력서 업로드 (0:00~0:20)
  2. Resume Agent 질문 생성 (0:20~0:40)
  3. 답변 입력 (0:40~1:00)
  4. Stress Agent 꼬리질문 (1:00~1:20)
  5. 평가 점수 출력 (1:20~1:40)
  6. 피드백 확인 (1:40~2:00)
- [ ] 유튜브 업로드 (unlisted)
- [ ] 링크 복사

---

### 🕖 새벽 7시 ~ 8시 (1시간) - 최종 점검 & 제출

**체크리스트**
- [ ] ① 기획서 PDF 제출
- [ ] ② GitHub 링크 제출 (README 확인)
- [ ] ③ 발표자료 PPT 제출
- [ ] ④ 시연영상 유튜브 링크 제출
- [ ] 모든 파일 용량 확인 (PDF < 10MB)
- [ ] 링크 클릭 테스트

---

## 📝 초간단 구현 예시 (통합 스크립트)

**main.py** (백엔드 없이 단일 파일로 전체 흐름)

```python
import json
from agents.resume_agent import ResumeAgent
from agents.stress_agent import StressAgent

# 1. 데이터 로드 (민영이 만든 파싱 결과)
with open('data/parsed_profile.json') as f:
    profile = json.load(f)

# 2. 에이전트 초기화
resume_agent = ResumeAgent()
stress_agent = StressAgent()

# 3. 면접 루프
conversation_history = []

for i in range(3):  # 3개 질문만
    print(f"\n=== 질문 {i+1} ===")
    
    # Resume Agent 질문
    context = {
        "profile": profile,
        "jd_requirements": profile["jd_requirements"],
        "conversation_history": conversation_history,
        "current_question_count": i
    }
    
    result = resume_agent.generate_question(context)
    print(f"면접관: {result['question']}")
    
    # 사용자 답변 입력
    answer = input("답변: ")
    
    # 평가 (간단하게)
    from agents.meta_agent import MetaAgent
    meta = MetaAgent()
    eval_result = meta.evaluate_answer(answer, result['question'])
    print(f"평가: {eval_result['overall_score']}/5 - {eval_result['feedback']}")
    
    # 히스토리 저장
    conversation_history.append({
        "question": result['question'],
        "answer": answer,
        "score": eval_result['overall_score']
    })
    
    # Stress 질문 (마지막 제외)
    if i < 2:
        stress_context = {
            "last_question": result['question'],
            "last_answer": answer
        }
        stress_result = stress_agent.generate_question(stress_context)
        print(f"면접관 (압박): {stress_result['question']}")
        
        stress_answer = input("답변: ")
        conversation_history.append({
            "question": stress_result['question'],
            "answer": stress_answer,
            "score": 3
        })

# 4. 최종 피드백
print("\n=== 면접 종료 ===")
avg_score = sum(h['score'] for h in conversation_history) / len(conversation_history)
print(f"평균 점수: {avg_score:.1f}/5")
print("강점: 구체적 사례 제시 우수")
print("약점: STAR 프레임 Result 부족")
```

---

## 🎬 시연 영상 스크립트 (2분)

**0:00~0:20 - 인트로**
- "안녕하세요, Solar Pro3 기반 AI 면접 에이전트입니다"
- 화면: 프로젝트 제목 + 팀 이름
- "이력서를 분석해 맞춤형 면접을 진행합니다"

**0:20~0:40 - 데이터 입력**
- 이력서 PDF 업로드 (또는 이미 파싱된 JSON 보여주기)
- "Document Parse로 이력서 구조 추출"
- 화면: profile JSON 일부

**0:40~1:20 - 면접 진행**
- Resume Agent 질문 1개
- 답변 입력 (타이핑 또는 미리 준비)
- Stress Agent 꼬리질문
- 답변 입력

**1:20~1:40 - 평가**
- 실시간 점수 출력
- "STAR 프레임 완성도 분석"
- 화면: 평가 결과

**1:40~2:00 - 피드백**
- 최종 점수 + 강약점
- "Multi-Agent 협업으로 동적 면접 구현"
- "감사합니다"

---

## 🚨 시간 부족 시 긴급 조치

### 새벽 4시까지 통합 안 되면

**Plan B: 데모 영상만 만들기**
1. 코드는 GitHub에 올리되 "WIP" 표시
2. PPT에 "구현 계획" 슬라이드 추가
3. 시연 영상을 "예상 시나리오" 시뮬레이션으로 제작
   - 질문/답변 미리 작성
   - 화면 전환으로 흐름만 보여주기

### 새벽 6시까지 시연 영상 못 만들면

**Plan C: 슬라이드에 스크린샷**
1. 영상 대신 PPT에 스크린샷 5~6장
2. "기술 구현 완료, 시연 환경 이슈로 스크린샷 제출" 명시
3. 심사 때 라이브 시연 약속

---

## 📋 기획서 HWP 양식 작성 팁

**분량**: 5~7페이지 권장 (과하지 않게)

**필수 섹션**:
1. **문제 정의** (1페이지)
   - 현재 면접 준비의 문제점
   - 타겟 사용자

2. **솔루션** (2페이지)
   - Multi-Agent 구조 다이어그램
   - 각 에이전트 역할 요약 (표)
   - 차별화 포인트 (왜 Agent인가)

3. **기술 구현** (1.5페이지)
   - Upstage API 활용 (표)
   - 외부 API (STT/TTS는 "향후 구현"으로)
   - 데이터 흐름도

4. **비즈니스 모델** (0.5페이지)
   - B2C → B2B 확장 가능성
   - 시장 규모

5. **향후 계획** (0.5페이지)
   - 음성 추가
   - RAG 기반 Trend Agent
   - 기업 HR 도구 전환

**PDF 변환**: HWP 완성 → 파일 → PDF로 저장

---

## ✅ 제출 전 최종 체크

### GitHub
- [ ] README.md 있음 (설치 방법, 실행 방법)
- [ ] requirements.txt 있음
- [ ] .env.example 있음 (API 키 가이드)
- [ ] 주석 달림
- [ ] 커밋 메시지 정리됨

### PPT
- [ ] 10슬라이드 이하 (간결하게)
- [ ] 폰트 일관성
- [ ] 다이어그램 명확함
- [ ] 스크린샷 선명함

### 시연 영상
- [ ] 2~3분 (너무 길지 않게)
- [ ] 화면 해상도 OK (1080p 권장)
- [ ] 음성 또는 자막 있음
- [ ] 유튜브 unlisted 설정

### 기획서
- [ ] PDF 변환 확인
- [ ] 페이지 번호 있음
- [ ] 오타 체크
- [ ] 파일명: 팀명_기획서.pdf

---

## 🎯 핵심 메시지 (발표/기획서 공통)

1. **문제**: 면접 준비는 고비용·비개인화
2. **솔루션**: Multi-Agent가 동적으로 적응하는 면접
3. **차별화**: 단순 챗봇 아님, 계획→실행→평가→조정 자동화
4. **기술**: Upstage 4개 API 풀 활용 (Document Parse/Extract/Solar/Embeddings)
5. **임팩트**: B2C 취준생 → B2B 기업 HR로 확장 가능

---

## 💡 조언

1. **완벽주의 버리기**: 8시간 남았음. 되는 것만 집중.
2. **음성 포기**: STT/TTS 통합은 시간 잡아먹는 늪.
3. **텍스트만 완성**: 텍스트 Q&A가 완벽하면 음성은 "향후 구현".
4. **시연 영상이 핵심**: 코드 안 돌아도 영상이 좋으면 통과 가능.
5. **기획서는 스토리**: 기술 나열 말고 "왜→무엇→어떻게" 스토리 구성.

---

**지금 당장 할 일**:
1. 팀 채팅방에 이 문서 공유
2. 역할 재확인
3. 10시까지 목표 정하기
4. 타이머 켜고 시작

화이팅! 🔥
