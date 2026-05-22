"""Speech-to-Text via OpenAI."""
import logging
from pathlib import Path

from openai import OpenAI

from app.config import settings


logger = logging.getLogger(__name__)


def transcribe_audio(audio_path: Path, language: str = "ko") -> dict:
    """
    Returns:
        {"status": "success", "transcript": str, "provider": str}
        {"status": "failed",  "error": str}
    """
    if not settings.openai_api_key:
        return {"status": "failed", "error": "OPENAI_API_KEY is not configured"}

    client = OpenAI(api_key=settings.openai_api_key)
    try:
        with audio_path.open("rb") as f:
            resp = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=f,
                language=language,
                response_format="text",
            )
        transcript = resp if isinstance(resp, str) else getattr(resp, "text", "")
        return {
            "status": "success",
            "transcript": transcript.strip(),
            "provider": "openai-gpt-4o-mini-transcribe",
        }
    except Exception as e:
        logger.exception("STT failed: %s", audio_path)
        return {"status": "failed", "error": str(e)}

