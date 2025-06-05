from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends
import os
import tempfile
from typing import Any, Dict

from src.config.env_config_provider import EnvConfigProvider
from src.config.config_validator import ConfigValidator
from src.factory import AutoMeetAIFactory
from src.models.transcription_result import TranscriptionResult
from src.exceptions import AutoMeetAIError
from src.utils.logging import configure_logger, get_logger

configure_logger()
logger = get_logger(__name__)

app = FastAPI(title="AutoMeetAI Transcription Service")

# Authentication token from environment
_config = EnvConfigProvider()
API_AUTH_TOKEN = _config.get("api_auth_token")
if API_AUTH_TOKEN:
    try:
        API_AUTH_TOKEN = ConfigValidator.validate_api_key(API_AUTH_TOKEN, "API Auth")
    except ValueError as exc:
        logger.warning(f"Invalid API authentication token: {exc}")
        # Continue using the original token instead of setting it to None



def require_api_key(x_api_key: str = Header(None)) -> None:
    """Validates the API key provided by the client."""
    if not API_AUTH_TOKEN:
        logger.error("API authentication token is not configured.")
        raise HTTPException(status_code=500, detail="API authentication not configured")
    if x_api_key != API_AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API key")


factory = AutoMeetAIFactory()
automeetai = factory.create()


@app.get("/health")
def health() -> Dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}


@app.post("/transcriptions", dependencies=[Depends(require_api_key)])
async def transcribe(
    file: UploadFile = File(...),
    speaker_labels: bool = True,
    speakers_expected: int = 2,
    language_code: str = "pt",
) -> Dict[str, Any]:
    """Process a video file and return its transcription."""
    temp_path = None
    try:
        suffix = os.path.splitext(file.filename)[1] or ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            temp_path = tmp.name

        transcription = automeetai.process_video(
            video_file=temp_path,
            transcription_config={
                "speaker_labels": speaker_labels,
                "speakers_expected": speakers_expected,
                "language_code": language_code,
            },
        )
        if not transcription:
            raise HTTPException(status_code=500, detail="Transcription failed")
        return {
            "text": transcription.text,
            "utterances": [
                {
                    "speaker": u.speaker,
                    "text": u.text,
                    "start": u.start,
                    "end": u.end,
                }
                for u in transcription.utterances
            ],
        }
    except AutoMeetAIError as exc:
        logger.error(f"Error processing transcription: {exc}")
        message = getattr(exc, "user_friendly_message", str(exc))
        raise HTTPException(status_code=400, detail=message) from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                logger.warning(f"Failed to remove temporary file {temp_path}")
