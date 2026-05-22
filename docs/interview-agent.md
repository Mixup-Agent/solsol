# Interview Agent Project

Solar Pro3 기반 AI 면접 에이전트 시스템

## 빠른 시작

### 1. 환경 설정

```bash
# 의존성 설치
pip install -r requirements.txt

# .env 파일 생성 (API 키 입력)
cp .env.example .env
# .env 파일을 열어서 UPSTAGE_API_KEY를 실제 값으로 변경
```

### 2. API 키 발급

1. Upstage Console 접속: https://console.upstage.ai/
2. 회원가입 후 API 키 발급
3. `.env` 파일에 키 입력:
   ```
   UPSTAGE_API_KEY=up_xxxxxxxxxxxxx
   ```

### 3. 테스트 실행

```bash
# Base Agent 테스트
cd agents
python base_agent.py

# Resume Agent 테스트
python resume_agent.py
```

## 프로젝트 구조

```
interview-agent-project/
├── agents/
│   ├── base_agent.py         # 기본 에이전트 클래스
│   ├── resume_agent.py       # 이력서 검증 에이전트
│   ├── stress_agent.py       # 압박 질문 에이전트 (TODO)
│   ├── trend_agent.py        # 트렌드 질문 에이전트 (TODO)
│   └── meta_agent.py         # 총괄 오케스트레이터 (TODO)
├── data/
│   └── sample_profile.json   # 테스트용 샘플 데이터
├── tests/
│   └── test_agents.py        # 통합 테스트 (TODO)
├── requirements.txt          # Python 의존성
├── .env.example             # 환경변수 템플릿
└── README.md               # 이 파일
```

## 개발 일정

### Day 1 오전
- [x] 프로젝트 세팅
- [x] Base Agent 구현
- [x] Resume Agent 구현
- [ ] Resume Agent 테스트 및 프롬프트 튜닝

### Day 1 오후
- [ ] Stress Agent 구현
- [ ] Meta Agent 기본 로직
- [ ] 백엔드 연동 준비

### Day 1 저녁
- [ ] 통합 테스트
- [ ] 3개 에이전트 동작 확인

### Day 2
- [ ] Trend Agent (선택)
- [ ] 음성 인터페이스 통합
- [ ] 최종 테스트 및 시연 준비

## API 사용 예시

```python
from agents.resume_agent import ResumeAgent

# 에이전트 초기화
agent = ResumeAgent()

# 컨텍스트 준비
context = {
    "profile": {...},
    "jd_requirements": {...},
    "conversation_history": [],
    "current_question_count": 0
}

# 질문 생성
result = agent.generate_question(context)
print(result['question'])
```

## 문제 해결

### API 키 오류
```
ValueError: UPSTAGE_API_KEY not found in environment variables
```
→ `.env` 파일에 API 키가 제대로 입력되었는지 확인

### 모듈 import 오류
```
ModuleNotFoundError: No module named 'dotenv'
```
→ `pip install -r requirements.txt` 실행

### JSON 파싱 오류
→ Solar API 응답 형식 확인, fallback 로직 작동 확인
