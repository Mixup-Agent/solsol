# Upstage API 실전 명세 가이드

## 📌 개요

에이전트 구현에 필요한 Upstage API 4개:

1. **Solar Pro3** - LLM (질문 생성, 평가, reasoning)
2. **Document Parse** - PDF → HTML/Markdown 변환
3. **Information Extract** - 구조화된 정보 추출 (선택)
4. **Embeddings** - 텍스트 임베딩 (유사도 계산)

---

## 1. Solar Pro3 API (LLM)

### 기본 정보

- **Model ID**: `solar-pro3`
- **Context Window**: 128,000 tokens
- **Parameters**: 102B total, 12B active (MoE)
- **언어**: 한국어 최적화, 영어·일본어 지원
- **가격**: 무료 (2026년 3월 2일까지)

### API 엔드포인트

```python
# OpenAI 호환 방식
url = "https://api.upstage.ai/v1/solar/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "solar-pro3",  # 또는 "solar-mini" (경량 버전)
    "messages": [
        {"role": "system", "content": "당신은 면접관입니다."},
        {"role": "user", "content": "질문을 생성해주세요."}
    ],
    "temperature": 0.7,  # 0.0~1.0
    "max_tokens": 1500,
    "top_p": 0.9,
    "stream": False  # True면 스트리밍
}

response = requests.post(url, headers=headers, json=payload)
result = response.json()

# 응답 구조
{
    "id": "chatcmpl-xxx",
    "object": "chat.completion",
    "created": 1234567890,
    "model": "solar-pro3",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "생성된 질문 텍스트..."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 50,
        "completion_tokens": 100,
        "total_tokens": 150
    }
}
```

### 너의 코드에서 사용

```python
# agents/base_agent.py
def call_solar(self, system_prompt: str, user_message: str) -> str:
    url = "https://api.upstage.ai/v1/solar/chat/completions"

    headers = {
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "solar-pro3",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "max_tokens": 1500
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"]
```

### 주의사항

- `temperature`: 질문 생성은 0.7, 평가는 0.3 권장
- `max_tokens`: 너무 적으면 중간에 잘림 (최소 1000)
- 에러 처리 필수 (API 장애, 토큰 초과 등)

---

## 2. Document Parse API

### 기본 정보

- **용도**: PDF/이미지 → HTML/Markdown 변환
- **지원 형식**: PDF, JPEG, PNG, TIFF, Office 파일
- **특징**: 표·차트·레이아웃 구조 보존

### API 엔드포인트

```python
url = "https://api.upstage.ai/v1/document-ai/document-parse"

headers = {
    "Authorization": f"Bearer {API_KEY}"
}

# 파일 업로드
files = {
    "document": open("/path/to/resume.pdf", "rb")
}

# 옵션 (선택)
data = {
    "ocr": "auto",  # "auto" | "force" (이미지 OCR 강제)
    "output_format": "html"  # "html" | "markdown"
}

response = requests.post(url, headers=headers, files=files, data=data)
result = response.json()

# 응답 구조
{
    "api": "document-parse",
    "status": "succeeded",
    "pages": [
        {
            "id": 1,
            "html": "<html>...<table>...</table>...</html>",
            "elements": [
                {
                    "type": "paragraph",
                    "text": "경력사항",
                    "bbox": [100, 200, 500, 250]
                },
                {
                    "type": "table",
                    "text": "<table>...</table>",
                    "bbox": [100, 300, 500, 600]
                }
            ]
        }
    ]
}
```

### 나경이 사용할 코드 예시

```python
def parse_resume(pdf_path: str) -> dict:
    """이력서 PDF 파싱"""
    url = "https://api.upstage.ai/v1/document-ai/document-parse"

    headers = {"Authorization": f"Bearer {API_KEY}"}
    files = {"document": open(pdf_path, "rb")}
    data = {"output_format": "html", "ocr": "auto"}

    response = requests.post(url, headers=headers, files=files, data=data)
    result = response.json()

    # HTML 추출
    html_content = ""
    for page in result["pages"]:
        html_content += page["html"]

    return {
        "raw_html": html_content,
        "pages": len(result["pages"]),
        "elements": result["pages"][0]["elements"]  # 첫 페이지 구조
    }
```

### 출력 예시 (elements)

```json
{
    "type": "paragraph",
    "text": "2021.03 - 2023.06 스타트업 A / 백엔드 엔지니어",
    "bbox": [100, 200, 500, 230],
    "category": "experience"  # 자동 분류 (선택)
}
```

---

## 3. Information Extract API (선택)

### 기본 정보

- **용도**: 문서에서 특정 정보 추출 (이름, 날짜, 금액 등)
- **Document Parse와 차이**: Parse는 전체 구조, Extract는 특정 필드

### API 엔드포인트

```python
url = "https://api.upstage.ai/v1/document-ai/information-extraction"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "document": "base64_encoded_pdf",  # 또는 URL
    "schema": {
        "name": "string",
        "education": "array",
        "experience": "array",
        "skills": "array"
    }
}

response = requests.post(url, headers=headers, json=payload)
```

### 나경이 사용 여부

- **시간 부족하면 생략** → Document Parse만으로 충분
- **시간 남으면** → 정확한 필드 추출 위해 사용

---

## 4. Embeddings API

### 기본 정보

- **용도**: 텍스트 → 벡터 변환 (유사도 계산용)
- **Model**: `solar-embedding-1-large`
- **Dimension**: 4096

### API 엔드포인트

```python
url = "https://api.upstage.ai/v1/solar/embeddings"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "solar-embedding-1-large",
    "input": [
        "Python 3년 실무 경험",
        "RESTful API 설계 능력"
    ]
}

response = requests.post(url, headers=headers, json=payload)
result = response.json()

# 응답 구조
{
    "object": "list",
    "data": [
        {
            "object": "embedding",
            "index": 0,
            "embedding": [0.123, -0.456, ...]  # 4096차원 벡터
        },
        {
            "object": "embedding",
            "index": 1,
            "embedding": [0.789, -0.321, ...]
        }
    ],
    "model": "solar-embedding-1-large",
    "usage": {
        "prompt_tokens": 20,
        "total_tokens": 20
    }
}
```

### Interview Planner에서 사용

```python
import numpy as np

def calculate_similarity(text1: str, text2: str) -> float:
    """두 텍스트 유사도 계산"""
    url = "https://api.upstage.ai/v1/solar/embeddings"

    payload = {
        "model": "solar-embedding-1-large",
        "input": [text1, text2]
    }

    response = requests.post(url, headers=headers, json=payload)
    data = response.json()["data"]

    # 벡터 추출
    vec1 = np.array(data[0]["embedding"])
    vec2 = np.array(data[1]["embedding"])

    # 코사인 유사도
    similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    return float(similarity)

# 사용 예시
resume_text = "Python 3년 실무 경험"
jd_requirement = "Python 전문가 우대"
score = calculate_similarity(resume_text, jd_requirement)
# score: 0.85 (높을수록 유사)
```

---

## 🔑 API 키 발급

1. https://console.upstage.ai/ 접속
2. 회원가입 / 로그인
3. 좌측 메뉴 → "API Keys" 클릭
4. "Create API Key" 클릭
5. 키 복사 → `.env` 파일에 저장

```bash
# .env
UPSTAGE_API_KEY=up_xxxxxxxxxxxxxxxxxxxxx
```

---

## 💡 에이전트 구현 시 필요한 것

### Resume Agent

- ✅ **Solar Pro3**: 질문 생성
- ❌ Document Parse: 나경이 처리한 profile JSON만 받음
- ❌ Embeddings: 필요 없음

### Stress Agent

- ✅ **Solar Pro3**: 압박 질문 생성
- ❌ 나머지: 필요 없음

### Interview Planner (나경)

- ✅ **Solar Pro3**: gap 분석
- ✅ **Embeddings**: 이력서↔JD 유사도
- ✅ **Document Parse**: 나경이 이력서 파싱

### Meta Agent (나경)

- ✅ **Solar Pro3**: 다음 에이전트 결정, 평가

---

## 🚨 에러 처리

### 공통 에러

```python
try:
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        print("API 키 오류")
    elif e.response.status_code == 429:
        print("Rate limit 초과 (너무 많이 호출)")
    elif e.response.status_code == 500:
        print("Upstage 서버 에러")
except requests.exceptions.Timeout:
    print("타임아웃 (30초 초과)")
except Exception as e:
    print(f"기타 에러: {e}")
```

---

## 📊 토큰 계산

### Solar Pro3 토큰 사용량

- **한국어**: 약 1.5~2 글자 = 1 token
- **영어**: 약 4~5 글자 = 1 token

**예시**:

```
시스템 프롬프트: "당신은 면접관입니다..." (약 200 tokens)
유저 메시지: 프로파일 + JD (약 500 tokens)
생성 응답: 질문 1개 (약 100 tokens)
-------------------------------------------------
총: 800 tokens → 무료라 상관없음
```

---

## ✅ 체크리스트

에이전트 구현 전 확인:

- [ ] API 키 발급 완료
- [ ] `.env` 파일에 키 저장
- [ ] `base_agent.py`에서 Solar 호출 테스트
- [ ] Document Parse는 나경이 담당 확인
- [ ] Embeddings는 시간 남으면 (선택)

---

**지금 Solar Pro3 API 호출 테스트부터 해봐. `python agents/base_agent.py`**
