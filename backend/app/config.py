from pathlib import Path

from pydantic_settings import BaseSettings

# config.py 위치: backend/app/config.py
#   parents[1] = backend/ , parents[2] = 레포 루트
_BACKEND_DIR = Path(__file__).resolve().parents[1]
_ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379"
    session_ttl: int = 7200
    upstage_api_key: str = ""
    openai_api_key: str = ""
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    class Config:
        # 실행 폴더와 무관하게 .env를 찾도록 절대경로 사용.
        # 레포 루트와 backend/ 둘 다 지원하며, 뒤쪽(backend/.env)이 우선한다.
        env_file = (str(_ROOT_DIR / ".env"), str(_BACKEND_DIR / ".env"))
        extra = "ignore"


settings = Settings()
