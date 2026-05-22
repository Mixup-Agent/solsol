from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from app.routers import interview, interview_sessions, interview_turns, session
from app.services.session_store import init_redis, close_redis, get_redis
from app.services.interview_db import init_interview_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    init_interview_db()
    yield
    await close_redis()


app = FastAPI(title="ShipYak Interview API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session.router, prefix="/api/v1")
app.include_router(interview.router, prefix="/api/v1")
app.include_router(interview_sessions.router, prefix="/api/v1")
app.include_router(interview_turns.router)

tts_dir = Path(__file__).resolve().parent / "app" / "data" / "tts"
tts_dir.mkdir(parents=True, exist_ok=True)
app.mount("/api/audio/tts", StaticFiles(directory=str(tts_dir)), name="tts_audio")


@app.get("/health")
async def health():
    try:
        redis = get_redis()
        await redis.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "disconnected"
    return {"status": "ok", "redis": redis_status}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
