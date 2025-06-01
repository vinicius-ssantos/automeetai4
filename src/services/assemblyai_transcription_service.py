from typing import Optional, Dict, Any, List, Union
import assemblyai as aai
from src.interfaces.transcription_service import TranscriptionService
from src.interfaces.config_provider import ConfigProvider
from src.utils.file_utils import validate_file_path
from src.utils.rate_limiter import RateLimiterRegistry
from src.utils.logging import get_logger
from src.models.transcription_result import TranscriptionResult
from src.adapters.assemblyai_adapter import AssemblyAIAdapter
from src.exceptions import (
    FileError, FileNotFoundError as AutoMeetAIFileNotFoundError,
    APIError, NetworkError, RateLimitError, TranscriptionFailedError
)
from src.config.default_config import (
    ASSEMBLYAI_API_KEY,
    DEFAULT_LANGUAGE_CODE,
    DEFAULT_SPEAKER_LABELS,
    DEFAULT_SPEAKERS_EXPECTED,
    ASSEMBLYAI_RATE_LIMIT,
    ASSEMBLYAI_RATE_LIMIT_PER,
    ASSEMBLYAI_RATE_LIMIT_BURST
)


class AssemblyAITranscriptionService(TranscriptionService):
    """
    Implementation of TranscriptionService using AssemblyAI.
    Following the Single Responsibility Principle, this class is only responsible
    for transcribing audio files.
    """

    # Initialize logger for this class
    logger = get_logger(__name__)

    def __init__(self, config_provider: Optional[ConfigProvider] = None):
        """
        Initialize the transcription service.

        Args:
            config_provider: Optional configuration provider
        """
        self.config_provider = config_provider

        # Set API key from config provider or default
        api_key = None
        if self.config_provider:
            api_key = self.config_provider.get("assemblyai_api_key", ASSEMBLYAI_API_KEY)
        else:
            api_key = ASSEMBLYAI_API_KEY

        # Validate API key
        self._validate_api_key(api_key)

        if api_key:
            aai.settings.api_key = api_key

    def _validate_api_key(self, api_key: Optional[str]) -> None:
        """
        Validate the API key.

        Args:
            api_key: The API key to validate

        Raises:
            ValueError: If the API key is invalid
        """
        if not api_key:
            raise ValueError("AssemblyAI API key is required. Please set the AUTOMEETAI_ASSEMBLYAI_API_KEY environment variable or provide it directly.")

        if not isinstance(api_key, str):
            raise ValueError("AssemblyAI API key must be a string.")

        if len(api_key.strip()) < 10:  # Basic validation for key length
            raise ValueError("AssemblyAI API key appears to be invalid. Please check your API key.")

    def transcribe(self, audio_file: str, config: Optional[Dict[str, Any]] = None,
                 allowed_audio_extensions: Optional[List[str]] = None) -> Union[TranscriptionResult, None]:
        """
        Transcribe an audio file to text using AssemblyAI.

        Args:
            audio_file: Path to the audio file to transcribe
            config: Optional configuration parameters for the transcription
            allowed_audio_extensions: Optional list of allowed audio file extensions

        Returns:
            TranscriptionResult: The transcription result, or None if transcription failed
        """
        transcript = None
        try:
            # Set default allowed extensions if not provided
            if allowed_audio_extensions is None:
                allowed_audio_extensions = ["mp3", "wav", "ogg", "flac", "m4a"]

            # Validate the audio file path
            validate_file_path(audio_file, allowed_extensions=allowed_audio_extensions)

            # Set default configuration
            transcription_config = {
                "speaker_labels": DEFAULT_SPEAKER_LABELS,
                "speakers_expected": DEFAULT_SPEAKERS_EXPECTED,
                "language_code": DEFAULT_LANGUAGE_CODE
            }

            # Override with provided config if any
            if config:
                transcription_config.update(config)

            # Create AssemblyAI config object
            aai_config = aai.TranscriptionConfig(
                speaker_labels=transcription_config["speaker_labels"],
                speakers_expected=transcription_config["speakers_expected"],
                language_code=transcription_config["language_code"]
            )

            # Get rate limiter for AssemblyAI
            rate_limiter = RateLimiterRegistry().get_limiter(
                "assemblyai",
                rate=ASSEMBLYAI_RATE_LIMIT,
                per=ASSEMBLYAI_RATE_LIMIT_PER,
                burst=ASSEMBLYAI_RATE_LIMIT_BURST
            )

            # Wait for a token to become available (rate limiting)
            rate_limiter.consume(wait=True)

            # Create transcriber and transcribe
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(
                audio_file,
                config=aai_config
            )

        except FileNotFoundError:
            error_msg = f"The audio file '{audio_file}' was not found."
            self.logger.error(error_msg)
            return None

        except ValueError as e:
            error_msg = f"Invalid audio file or configuration: {e}"
            self.logger.error(error_msg)
            return None

        except Exception as e:
            # Handle specific AssemblyAI exceptions by checking the exception class name and string representation
            exception_class_name = e.__class__.__name__
            exception_str = str(e).lower()

            # Check for authentication errors
            if exception_class_name == "AuthenticationError" or "authentication" in exception_str or "api key" in exception_str:
                error_msg = f"AssemblyAI authentication error: {e}"
                self.logger.error(error_msg)
                return None

            # Check for rate limit errors
            elif exception_class_name == "RateLimitError" or "rate limit" in exception_str:
                error_msg = f"AssemblyAI rate limit exceeded: {e}"
                self.logger.error(error_msg)
                return None

            # Check for timeout errors
            elif exception_class_name == "RequestTimeoutError" or "timeout" in exception_str:
                error_msg = f"AssemblyAI request timeout: {e}"
                self.logger.error(error_msg)
                return None

            # Check for API errors
            elif exception_class_name == "APIError" or "api error" in exception_str:
                error_msg = f"AssemblyAI API error: {e}"
                self.logger.error(error_msg)
                return None

            # Handle all other exceptions
            else:
                error_msg = f"An error occurred during transcription: {e}"
                self.logger.error(error_msg)
                return None

        # Only convert to TranscriptionResult if transcript is valid and not an exception
        if transcript and not isinstance(transcript, Exception) and hasattr(transcript, 'text'):
            return AssemblyAIAdapter.convert(transcript, audio_file)
        return None
