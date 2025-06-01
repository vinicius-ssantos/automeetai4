from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from src.models.transcription_result import Utterance, TranscriptionResult


@dataclass
class StreamingTranscriptionResult:
    """
    Representa o resultado parcial de uma transcrição em streaming.
    """
    text: str
    is_final: bool
    confidence: float = 1.0
    speaker: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte o resultado para um dicionário.
        
        Returns:
            Dict[str, Any]: O resultado como um dicionário
        """
        return {
            "text": self.text,
            "is_final": self.is_final,
            "confidence": self.confidence,
            "speaker": self.speaker,
            "start_time": self.start_time,
            "end_time": self.end_time
        }


class StreamingSession:
    """
    Representa uma sessão de transcrição em streaming.
    Mantém o estado da sessão e acumula resultados parciais.
    """
    
    def __init__(self):
        """
        Inicializa uma nova sessão de streaming.
        """
        self.partial_results: List[StreamingTranscriptionResult] = []
        self.final_results: List[StreamingTranscriptionResult] = []
        self.is_active: bool = False
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def add_result(self, result: StreamingTranscriptionResult) -> None:
        """
        Adiciona um resultado parcial à sessão.
        
        Args:
            result: O resultado parcial a ser adicionado
        """
        if result.is_final:
            self.final_results.append(result)
        else:
            self.partial_results.append(result)
    
    def get_current_text(self) -> str:
        """
        Obtém o texto atual da transcrição, combinando resultados finais e o último parcial.
        
        Returns:
            str: O texto atual da transcrição
        """
        # Texto de todos os resultados finais
        final_text = " ".join([r.text for r in self.final_results])
        
        # Adiciona o texto do último resultado parcial, se houver
        if self.partial_results:
            if final_text:
                return f"{final_text} {self.partial_results[-1].text}"
            else:
                return self.partial_results[-1].text
        
        return final_text
    
    def to_transcription_result(self, audio_file: str = "") -> TranscriptionResult:
        """
        Converte a sessão de streaming em um TranscriptionResult.
        
        Args:
            audio_file: O caminho para o arquivo de áudio (opcional)
            
        Returns:
            TranscriptionResult: O resultado da transcrição
        """
        utterances = []
        
        # Converte resultados finais em utterances
        for result in self.final_results:
            utterances.append(Utterance(
                speaker=result.speaker or "Speaker 1",
                text=result.text,
                start=result.start_time,
                end=result.end_time
            ))
        
        # Se não houver resultados finais, mas houver parciais, use o último parcial
        if not utterances and self.partial_results:
            last_partial = self.partial_results[-1]
            utterances.append(Utterance(
                speaker=last_partial.speaker or "Speaker 1",
                text=last_partial.text,
                start=last_partial.start_time,
                end=last_partial.end_time
            ))
        
        # Cria o TranscriptionResult
        return TranscriptionResult(
            utterances=utterances,
            text=self.get_current_text(),
            audio_file=audio_file
        )