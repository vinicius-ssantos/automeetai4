from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Union

from src.models.transcription_result import TranscriptionResult


class TranscriptionService(ABC):
    """
    Interface for audio transcription services.
    Following the Interface Segregation Principle, this interface defines
    only the methods needed for audio transcription.
    """

    @abstractmethod
    def transcribe(self, audio_file: str, config: Optional[Dict[str, Any]] = None,
                 allowed_audio_extensions: Optional[List[str]] = None) -> Union[TranscriptionResult, None]:
        """
        Transcribe an audio file to text.

        Args:
            audio_file: Path to the audio file to transcribe
            config: Optional configuration parameters for the transcription
            allowed_audio_extensions: Optional list of allowed audio file extensions

        Returns:
            TranscriptionResult: The transcription result, or None if transcription failed
        """
        pass
