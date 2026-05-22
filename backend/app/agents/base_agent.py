import os
import requests
import json
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class BaseAgent:
    """모든 에이전트의 기본 클래스"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.api_key = os.getenv("UPSTAGE_API_KEY")
        
        if not self.api_key:
            raise ValueError("UPSTAGE_API_KEY not found in environment variables")
        
        self.base_url = "https://api.upstage.ai/v1/solar"
        
    def call_solar(self, 
                   system_prompt: str, 
                   user_message: str,
                   temperature: float = 0.7,
                   max_tokens: int = 1500) -> str:
        """
        Solar Pro3 API 호출
        
        Args:
            system_prompt: 시스템 프롬프트
            user_message: 사용자 메시지
            temperature: 0.0~1.0 (낮을수록 deterministic)
            max_tokens: 최대 토큰 수
            
        Returns:
            str: 모델 응답 텍스트
        """
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "solar-pro",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            print(f"[{self.agent_name}] Calling Solar API...")
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            print(f"[{self.agent_name}] Response received ({len(content)} chars)")
            
            return content
        
        except requests.exceptions.RequestException as e:
            error_msg = f"API Request Error: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg += f"\nDetail: {error_detail}"
                except:
                    error_msg += f"\nStatus: {e.response.status_code}"
            
            print(f"[{self.agent_name}] {error_msg}")
            raise Exception(error_msg)
    
    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Solar 응답에서 JSON 추출 (```json 태그 제거)
        
        Args:
            response: Solar API 응답 텍스트
            
        Returns:
            dict: 파싱된 JSON
        """
        # ```json ... ``` 제거
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"[{self.agent_name}] JSON Parse Error: {e}")
            print(f"Raw response: {response[:200]}...")
            raise
    
    def generate_question(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        각 에이전트가 오버라이드할 메서드
        
        Args:
            context: 에이전트별 필요 컨텍스트
            
        Returns:
            dict: 질문 결과
        """
        raise NotImplementedError(f"{self.agent_name} must implement generate_question()")


if __name__ == "__main__":
    # 간단한 테스트
    print("Testing BaseAgent...")
    
    try:
        agent = BaseAgent("Test Agent")
        print(f"✓ Agent initialized with API key: {agent.api_key[:10]}...")
        
        # 간단한 테스트 호출
        response = agent.call_solar(
            system_prompt="You are a helpful assistant.",
            user_message="Say 'Hello, I am working!' in Korean.",
            temperature=0.5,
            max_tokens=100
        )
        
        print(f"✓ API call successful!")
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
