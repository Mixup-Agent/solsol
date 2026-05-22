import sys
import os
sys.path.append(os.path.dirname(__file__))

from base_agent import BaseAgent
from typing import Dict, Any, List


class ResumeAgent(BaseAgent):
    """이력서 기반 검증 질문 에이전트"""
    
    def __init__(self):
        super().__init__("Resume Agent")
        
    def generate_question(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        이력서/자소서 기반 구체적 사실 검증 질문 생성
        
        Args:
            context: {
                "profile": {...},  # 지원자 프로파일
                "jd_requirements": {...},  # JD 요구사항
                "conversation_history": [...],  # 이전 대화
                "current_question_count": int  # 현재 질문 번호
            }
        
        Returns:
            {
                "question": str,
                "reasoning": str,
                "follow_up_strategy": str,
                "category": str
            }
        """
        
        profile = context.get("profile", {})
        jd = context.get("jd_requirements", {})
        history = context.get("conversation_history", [])
        question_count = context.get("current_question_count", 0)
        
        # 시스템 프롬프트
        system_prompt = self._build_system_prompt(profile)
        
        # 유저 메시지
        user_message = self._build_user_message(profile, jd, history, question_count)
        
        # Solar API 호출
        response = self.call_solar(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=0.7,
            max_tokens=1000
        )
        
        # JSON 파싱
        try:
            result = self.parse_json_response(response)
            
            # 필수 필드 검증
            if "question" not in result:
                raise ValueError("Response missing 'question' field")
            
            # 기본값 설정
            result.setdefault("reasoning", "검증 필요")
            result.setdefault("follow_up_strategy", "구체성 요구")
            result.setdefault("category", "경험 검증")
            
            return result
            
        except Exception as e:
            print(f"[{self.agent_name}] Parse error, using fallback: {e}")
            
            # 폴백 질문
            return self._get_fallback_question(profile, question_count)
    
    def _build_system_prompt(self, profile: Dict[str, Any]) -> str:
        """시스템 프롬프트 생성"""
        
        position = profile.get("target_position", "개발자")
        
        return f"""당신은 {position} 채용 면접관입니다.

**역할**:
- 지원자의 이력서, 자소서, 프로젝트를 기반으로 구체적 사실 검증 질문을 생성하세요.
- 모호한 표현이나 과장된 설명을 파고들어 구체성을 확보하세요.
- STAR 프레임워크(Situation, Task, Action, Result)가 완성되도록 유도하세요.

**질문 스타일**:
- 전문적이지만 위압적이지 않게
- "~하신 것으로 보이는데요" 같은 부드러운 진입
- 구체적 수치, 사례, 의사결정 과정을 물어보세요

**금지사항**:
- 추상적이거나 철학적인 질문 금지
- 이미 물어본 질문 반복 금지
- JD 요구사항과 무관한 질문 금지
- 네/아니오로 답할 수 있는 단순 질문 금지

**출력 형식** (반드시 JSON):
{{
  "question": "면접 질문 (자연스러운 한국어)",
  "reasoning": "이 질문을 선택한 이유 (내부용)",
  "follow_up_strategy": "답변이 약할 경우 후속 질문 전략",
  "category": "기술 검증 | 프로젝트 경험 | 문제 해결 | 협업"
}}"""
    
    def _build_user_message(self, 
                           profile: Dict[str, Any],
                           jd: Dict[str, Any],
                           history: List[Dict],
                           question_count: int) -> str:
        """유저 메시지 생성"""
        
        # 경력 요약
        experiences = profile.get("experience", [])
        exp_summary = self._format_experiences(experiences)
        
        # 프로젝트 요약
        projects = profile.get("projects", [])
        proj_summary = self._format_projects(projects)
        
        # JD 요구사항
        must_have = jd.get("must_have", [])
        jd_summary = "\n".join([f"- {item}" for item in must_have[:3]])
        
        # 대화 히스토리
        history_text = self._format_history(history)
        
        return f"""
**지원자 프로파일**:
- 목표 직무: {profile.get('target_position', '개발자')}
- 경력: {exp_summary}
- 주요 프로젝트: {proj_summary}
- 보유 스킬: {', '.join(profile.get('skills', [])[:5])}

**JD 핵심 요구사항**:
{jd_summary}

**이전 질문 이력** ({question_count}개):
{history_text}

---

위 정보를 바탕으로:

1. 지원자 경험 중 **가장 검증이 필요한 부분** 1개를 선택하세요
2. 그 부분을 파고드는 **구체적 질문 1개**를 생성하세요
3. 답변이 모호할 경우의 **follow-up 전략**을 제시하세요

중요: 반드시 JSON 형식으로만 응답하세요.
"""
    
    def _format_experiences(self, experiences: List[Dict]) -> str:
        """경력 포맷팅"""
        if not experiences:
            return "(경력 없음)"
        
        exp = experiences[0]  # 최근 경력만
        return f"{exp.get('company', 'N/A')} - {exp.get('role', 'N/A')} ({exp.get('duration', 'N/A')})"
    
    def _format_projects(self, projects: List[Dict]) -> str:
        """프로젝트 포맷팅"""
        if not projects:
            return "(프로젝트 없음)"
        
        proj = projects[0]  # 주요 프로젝트만
        return f"{proj.get('title', 'N/A')}"
    
    def _format_history(self, history: List[Dict]) -> str:
        """대화 히스토리 포맷팅"""
        if not history:
            return "(아직 질문 없음)"
        
        formatted = []
        for i, turn in enumerate(history[-3:], 1):  # 최근 3개만
            q = turn.get('question', '')[:80]
            formatted.append(f"{i}. {q}...")
        
        return "\n".join(formatted)
    
    def _get_fallback_question(self, profile: Dict, count: int) -> Dict[str, Any]:
        """폴백 질문 (API 실패 시)"""
        
        fallback_questions = [
            "자기소개서에서 가장 강조하신 경험에 대해 구체적으로 설명해주시겠어요?",
            "최근 진행하신 프로젝트에서 가장 어려웠던 기술적 문제와 해결 방법을 말씀해주세요.",
            "팀 프로젝트에서 의견 충돌이 있었던 경험과 해결 과정을 설명해주시겠어요?",
        ]
        
        question = fallback_questions[count % len(fallback_questions)]
        
        return {
            "question": question,
            "reasoning": "Fallback question (API error)",
            "follow_up_strategy": "구체적 수치나 사례 요구",
            "category": "일반 검증"
        }


if __name__ == "__main__":
    # 테스트 코드
    print("=== Resume Agent 테스트 ===\n")
    
    # 샘플 데이터
    test_context = {
        "profile": {
            "target_position": "백엔드 개발자",
            "experience": [{
                "company": "스타트업 A",
                "role": "백엔드 엔지니어",
                "duration": "2년 3개월"
            }],
            "projects": [{
                "title": "MSA 전환 프로젝트",
                "description": "모놀리식 아키텍처를 마이크로서비스로 전환",
                "tech_stack": ["Python", "FastAPI", "Docker", "Kubernetes"]
            }],
            "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"]
        },
        "jd_requirements": {
            "must_have": [
                "Python 3년 이상 경험",
                "RESTful API 설계 및 구현 경험",
                "데이터베이스 설계 및 최적화 경험"
            ],
            "nice_to_have": [
                "Kubernetes 경험",
                "MSA 아키텍처 설계 경험"
            ]
        },
        "conversation_history": [],
        "current_question_count": 0
    }
    
    try:
        agent = ResumeAgent()
        print("✓ Resume Agent 초기화 성공\n")
        
        # 질문 생성
        result = agent.generate_question(test_context)
        
        print("생성된 질문:")
        print(f"  질문: {result['question']}")
        print(f"  이유: {result['reasoning']}")
        print(f"  Follow-up: {result['follow_up_strategy']}")
        print(f"  카테고리: {result['category']}")
        
        print("\n✓ 테스트 성공!")
        
    except Exception as e:
        print(f"\n✗ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
