from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379"
    session_ttl: int = 7200
    anthropic_api_key: str = ""
    upstage_api_key: str = ""
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
