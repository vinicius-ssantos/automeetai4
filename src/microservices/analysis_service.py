from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Any, Dict

from src.config.env_config_provider import EnvConfigProvider
from src.config.config_validator import ConfigValidator
from src.factory import AutoMeetAIFactory
from src.models.transcription_result import TranscriptionResult
from src.exceptions import AutoMeetAIError
from src.utils.logging import configure_logger, get_logger

configure_logger()
logger = get_logger(__name__)

app = FastAPI(title="AutoMeetAI Analysis Service")

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
        logger.warning("API authentication token is not configured. API authentication is disabled.")
        return
    if x_api_key != API_AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API key")


factory = AutoMeetAIFactory()
automeetai = factory.create()


@app.get("/health")
def health() -> Dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}


class AnalysisRequest(BaseModel):
    """Request body for the analysis endpoint."""

    text: str
    system_prompt: str = "Você é um assistente de IA."
    user_prompt: str = "Analise a transcrição a seguir:\n{transcription}"


@app.post("/analysis", dependencies=[Depends(require_api_key)])
def analyze(request: AnalysisRequest) -> Dict[str, Any]:
    """Analyze a transcription text and return the result."""
    transcription = TranscriptionResult(utterances=[], text=request.text, audio_file="input.mp3")
    try:
        result = automeetai.analyze_transcription(
            transcription=transcription,
            system_prompt=request.system_prompt,
            user_prompt_template=request.user_prompt,
        )
        if result is None:
            raise HTTPException(status_code=500, detail="Analysis failed")
        return {"analysis": result}
    except AutoMeetAIError as exc:
        logger.error(f"Error processing analysis: {exc}")
        message = getattr(exc, "user_friendly_message", str(exc))
        raise HTTPException(status_code=400, detail=message) from exc
