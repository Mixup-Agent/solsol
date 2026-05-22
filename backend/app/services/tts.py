"""Text-to-Speech. ElevenLabs primary, OpenAI fallback."""
import logging
from pathlib import Path

import requests
from openai import OpenAI

from app.config import settings


logger = logging.getLogger(__name__)


def synthesize_speech(text: str, output_path: Path) -> dict:
    """ElevenLabs 우선. 키 없거나 실패하면 OpenAI TTS로 폴백."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if settings.elevenlabs_api_key:
        result = _tts_elevenlabs(text, output_path)
        if result["status"] == "success":
            return result
        logger.warning(
            "ElevenLabs failed, falling back to OpenAI: %s", result.get("error")
        )

    return _tts_openai(text, output_path)


def _tts_elevenlabs(text: str, output_path: Path) -> dict:
    try:
        url = (
            "https://api.elevenlabs.io/v1/text-to-speech/"
            f"{settings.elevenlabs_voice_id}"
        )
        r = requests.post(
            url,
            headers={
                "xi-api-key": settings.elevenlabs_api_key,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            },
            timeout=30,
        )
        r.raise_for_status()
        output_path.write_bytes(r.content)
        return {
            "status": "success",
            "file_path": str(output_path),
            "provider": "elevenlabs",
        }
    except Exception as e:
        logger.exception("ElevenLabs TTS failed")
        return {"status": "failed", "error": str(e)}


def _tts_openai(text: str, output_path: Path) -> dict:
    if not settings.openai_api_key:
        return {"status": "failed", "error": "OPENAI_API_KEY is not configured"}

    client = OpenAI(api_key=settings.openai_api_key)
    try:
        # voice: alloy/echo/onyx/nova/shimmer
        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="onyx",
            input=text,
            response_format="mp3",
        ) as resp:
            resp.stream_to_file(str(output_path))
        return {
            "status": "success",
            "file_path": str(output_path),
            "provider": "openai-gpt-4o-mini-tts",
        }
    except Exception as e:
        logger.exception("OpenAI TTS failed")
        return {"status": "failed", "error": str(e)}

