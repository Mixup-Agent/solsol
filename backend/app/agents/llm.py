"""에이전트 공용 LLM — Upstage Solar Pro.

모든 에이전트(resume·trend·stress·judge)가 이 인스턴스를 공유한다.
모델을 바꿀 일이 생기면 이 파일 한 곳만 수정하면 된다.
"""
from langchain_upstage import ChatUpstage

from app.config import settings

solar = ChatUpstage(model="solar-pro", api_key=settings.upstage_api_key)
