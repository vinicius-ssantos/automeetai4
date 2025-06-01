from typing import Any, Optional, List, Dict
from src.models.transcription_result import TranscriptionResult, Utterance


class WhisperAdapter:
    """
    Adaptador para converter transcrições do OpenAI Whisper para o modelo TranscriptionResult.
    """
    
    @staticmethod
    def convert(transcript: Any, audio_file: str) -> TranscriptionResult:
        """
        Converte uma transcrição do OpenAI Whisper para o modelo TranscriptionResult.
        
        Args:
            transcript: O objeto de transcrição do Whisper
            audio_file: O caminho para o arquivo de áudio que foi transcrito
            
        Returns:
            TranscriptionResult: Uma nova instância de TranscriptionResult
        """
        if not transcript:
            return TranscriptionResult(utterances=[], text="", audio_file=audio_file)
        
        # Extrair o texto completo da transcrição
        full_text = transcript.get("text", "")
        
        # Extrair os segmentos (se disponíveis)
        segments = transcript.get("segments", [])
        
        utterances = []
        
        if segments:
            # Se temos segmentos, criar utterances a partir deles
            for i, segment in enumerate(segments):
                start = segment.get("start")
                end = segment.get("end")
                text = segment.get("text", "").strip()
                
                if text:
                    # Como o Whisper não identifica falantes, usamos um padrão
                    speaker = "Speaker 1"
                    
                    utterances.append(Utterance(
                        speaker=speaker,
                        text=text,
                        start=start,
                        end=end
                    ))
        else:
            # Se não temos segmentos, criar uma única utterance com o texto completo
            utterances.append(Utterance(
                speaker="Speaker 1",
                text=full_text,
                start=None,
                end=None
            ))
        
        return TranscriptionResult(
            utterances=utterances,
            text=full_text,
            audio_file=audio_file
        )