from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from src.models.transcription_result import TranscriptionResult


class OutputFormatter(ABC):
    """
    Interface para formatadores de saída.
    Seguindo o padrão Strategy, esta interface define os métodos
    que os formatadores concretos devem implementar para formatar
    os resultados de transcrição de diferentes maneiras.
    """
    
    @abstractmethod
    def format(self, transcription: TranscriptionResult, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Formata um resultado de transcrição.
        
        Args:
            transcription: O resultado da transcrição a ser formatado
            options: Opções de formatação específicas para este formatador
            
        Returns:
            str: O resultado formatado
        """
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        """
        Obtém a extensão de arquivo para este formato.
        
        Returns:
            str: A extensão de arquivo (sem o ponto)
        """
        pass