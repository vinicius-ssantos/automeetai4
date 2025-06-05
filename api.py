from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header, Request
try:
    from starlette_graphene3 import GraphQLApp, make_playground_handler
except ImportError:
    # Provide a helpful error message
    raise ImportError(
        "The 'starlette_graphene3' module is not installed. "
        "Please install it with: pip install starlette-graphene3"
    )

import graphene
from pydantic import BaseModel
import os
import tempfile
from typing import Any, Dict, List

from src.config.env_config_provider import EnvConfigProvider
from src.config.config_validator import ConfigValidator

from src.factory import AutoMeetAIFactory
from src.models.transcription_result import TranscriptionResult, Utterance
from src.exceptions import AutoMeetAIError
from src.utils.logging import configure_logger, get_logger

configure_logger()
logger = get_logger(__name__)

app = FastAPI(title="AutoMeetAI API")


# API authentication token from configuration
_config = EnvConfigProvider()
API_AUTH_TOKEN = _config.get("api_auth_token")
if API_AUTH_TOKEN:
    try:
        API_AUTH_TOKEN = ConfigValidator.validate_api_key(API_AUTH_TOKEN, "API Auth")
    except ValueError as exc:
        logger.warning(f"Invalid API authentication token: {exc}")
        # Continue using the original token instead of setting it to None



def require_api_key(x_api_key: str = Header(None)) -> None:
    """Validate the API key provided in the request header."""
    if not API_AUTH_TOKEN:
        logger.warning("API authentication token is not configured. API authentication is disabled.")
        return
    if x_api_key != API_AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API key")

# Initialize AutoMeetAI using the factory
factory = AutoMeetAIFactory()
automeetai = factory.create()


def _transcription_to_dict(transcription: TranscriptionResult) -> Dict[str, Any]:
    """Convert a TranscriptionResult into a dictionary."""
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
    """Process a video file and return its transcription.

    Parameters are provided as query arguments to control the transcription
    behavior.
    """
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
        return _transcription_to_dict(transcription)
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


class AnalysisRequest(BaseModel):
    """Request body for the analysis endpoint."""

    text: str
    system_prompt: str = "Você é um assistente de IA."
    user_prompt: str = "Analise a transcrição a seguir:\n{transcription}"


@app.post("/analysis", dependencies=[Depends(require_api_key)])
def analyze(request: AnalysisRequest) -> Dict[str, Any]:
    """Analyze a transcription text using the AutoMeetAI services."""
    transcription = TranscriptionResult(
        utterances=[], text=request.text, audio_file="input.mp3"
    )
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


class Query(graphene.ObjectType):
    """GraphQL query definitions."""

    health = graphene.String()

    def resolve_health(self, info):
        return "ok"


class Mutations(graphene.ObjectType):
    """GraphQL mutations."""

    analyze = graphene.Field(
        graphene.String,
        text=graphene.String(required=True),
        system_prompt=graphene.String(default_value="Você é um assistente de IA."),
        user_prompt=graphene.String(default_value="Analise a transcrição a seguir:\n{transcription}"),
    )

    def resolve_analyze(self, info, text: str, system_prompt: str, user_prompt: str):
        transcription = TranscriptionResult(utterances=[], text=text, audio_file="input.mp3")
        try:
            return automeetai.analyze_transcription(
                transcription=transcription,
                system_prompt=system_prompt,
                user_prompt_template=user_prompt,
            )
        except AutoMeetAIError as exc:
            message = getattr(exc, "user_friendly_message", str(exc))
            raise Exception(message)


schema = graphene.Schema(query=Query, mutation=Mutations)
graphql_app = GraphQLApp(schema=schema, on_get=make_playground_handler())


@app.api_route("/graphql", methods=["GET", "POST"])
async def graphql_endpoint(request: Request, x_api_key: str = Header(None)):
    """GraphQL endpoint with API key validation."""
    require_api_key(x_api_key)
    if request.method == "GET":
        response = await graphql_app._get_on_get(request)
    else:
        response = await graphql_app._handle_http_request(request)
    return response
