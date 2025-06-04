from typing import Any, Optional
from src.models.transcription_result import TranscriptionResult, Utterance


class AssemblyAIAdapter:
    """
    Adaptador para converter transcrições do AssemblyAI para o modelo TranscriptionResult.
    """

    @staticmethod
    def convert(transcript: Any, audio_file: str) -> Optional[TranscriptionResult]:
        """
        Converte uma transcrição do AssemblyAI para o modelo TranscriptionResult.

        Args:
            transcript: O objeto de transcrição do AssemblyAI
            audio_file: O caminho para o arquivo de áudio que foi transcrito

        Returns:
            TranscriptionResult: Uma nova instância de TranscriptionResult, ou None se a transcrição for inválida
        """
        # Check if transcript is an exception or None
        if transcript is None or isinstance(transcript, Exception):
            return None

        # Check if transcript has the required attributes
        if not hasattr(transcript, 'utterances') or transcript.utterances is None:
            # Create a TranscriptionResult with empty utterances if transcript has text attribute
            if hasattr(transcript, 'text'):
                return TranscriptionResult(utterances=[], text=transcript.text, audio_file=audio_file)
            return None

        utterances = []
        for u in transcript.utterances or []:
            utterances.append(Utterance(
                speaker=f"Speaker {u.speaker}",
                text=u.text,
                start=u.start / 1000 if hasattr(u, 'start') and u.start is not None else None,  # Converter de ms para segundos
                end=u.end / 1000 if hasattr(u, 'end') and u.end is not None else None  # Converter de ms para segundos
            ))

        return TranscriptionResult(
            utterances=utterances,
            text=transcript.text if hasattr(transcript, 'text') else "",
            audio_file=audio_file
        )
