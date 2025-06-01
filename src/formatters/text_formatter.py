from typing import Dict, Any, Optional

from src.interfaces.output_formatter import OutputFormatter
from src.models.transcription_result import TranscriptionResult
from src.utils.logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)


class TextFormatter(OutputFormatter):
    """
    Formatador de saída para texto simples.
    Implementa a interface OutputFormatter para formatar resultados de transcrição como texto simples.
    """
    
    def format(self, transcription: TranscriptionResult, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Formata um resultado de transcrição como texto simples.
        
        Args:
            transcription: O resultado da transcrição a ser formatado
            options: Opções de formatação (opcional)
                - include_timestamps: Se True, inclui timestamps no início de cada fala
                - speaker_prefix: Prefixo a ser usado antes do nome do falante (padrão: "")
                - speaker_suffix: Sufixo a ser usado após o nome do falante (padrão: ": ")
                
        Returns:
            str: O resultado formatado como texto simples
        """
        if not transcription or not transcription.utterances:
            logger.warning("Tentativa de formatar uma transcrição vazia ou nula")
            return ""
            
        # Configurações padrão
        include_timestamps = False
        speaker_prefix = ""
        speaker_suffix = ": "
        
        # Aplicar opções personalizadas, se fornecidas
        if options:
            include_timestamps = options.get("include_timestamps", include_timestamps)
            speaker_prefix = options.get("speaker_prefix", speaker_prefix)
            speaker_suffix = options.get("speaker_suffix", speaker_suffix)
        
        result = []
        
        for utterance in transcription.utterances:
            line = ""
            
            # Adicionar timestamp, se solicitado
            if include_timestamps and utterance.start is not None:
                minutes = int(utterance.start / 60)
                seconds = int(utterance.start % 60)
                line += f"[{minutes:02d}:{seconds:02d}] "
            
            # Adicionar falante e texto
            line += f"{speaker_prefix}{utterance.speaker}{speaker_suffix}{utterance.text}"
            result.append(line)
        
        return "\n".join(result)
    
    def get_file_extension(self) -> str:
        """
        Obtém a extensão de arquivo para este formato.
        
        Returns:
            str: A extensão de arquivo (sem o ponto)
        """
        return "txt"