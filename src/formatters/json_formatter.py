import json
from typing import Dict, Any, Optional, List
from dataclasses import asdict

from src.interfaces.output_formatter import OutputFormatter
from src.models.transcription_result import TranscriptionResult, Utterance
from src.utils.logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)


class JSONFormatter(OutputFormatter):
    """
    Formatador de saída para JSON.
    Implementa a interface OutputFormatter para formatar resultados de transcrição como JSON.
    """
    
    def format(self, transcription: TranscriptionResult, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Formata um resultado de transcrição como JSON.
        
        Args:
            transcription: O resultado da transcrição a ser formatado
            options: Opções de formatação (opcional)
                - pretty_print: Se True, formata o JSON com indentação para melhor legibilidade (padrão: True)
                - include_metadata: Se True, inclui metadados como o arquivo de áudio (padrão: True)
                - include_full_text: Se True, inclui o texto completo além das falas individuais (padrão: True)
                
        Returns:
            str: O resultado formatado como JSON
        """
        if not transcription:
            logger.warning("Tentativa de formatar uma transcrição nula")
            return "{}"
            
        # Configurações padrão
        pretty_print = True
        include_metadata = True
        include_full_text = True
        
        # Aplicar opções personalizadas, se fornecidas
        if options:
            pretty_print = options.get("pretty_print", pretty_print)
            include_metadata = options.get("include_metadata", include_metadata)
            include_full_text = options.get("include_full_text", include_full_text)
        
        # Criar dicionário para o JSON
        result_dict: Dict[str, Any] = {}
        
        # Adicionar metadados, se solicitado
        if include_metadata:
            result_dict["metadata"] = {
                "audio_file": transcription.audio_file
            }
        
        # Adicionar texto completo, se solicitado
        if include_full_text:
            result_dict["text"] = transcription.text
        
        # Adicionar falas
        utterances_list: List[Dict[str, Any]] = []
        
        for utterance in transcription.utterances:
            utterance_dict = {
                "speaker": utterance.speaker,
                "text": utterance.text
            }
            
            # Adicionar timestamps, se disponíveis
            if utterance.start is not None:
                utterance_dict["start"] = utterance.start
            if utterance.end is not None:
                utterance_dict["end"] = utterance.end
                
            utterances_list.append(utterance_dict)
        
        result_dict["utterances"] = utterances_list
        
        # Converter para JSON
        indent = 2 if pretty_print else None
        return json.dumps(result_dict, indent=indent, ensure_ascii=False)
    
    def get_file_extension(self) -> str:
        """
        Obtém a extensão de arquivo para este formato.
        
        Returns:
            str: A extensão de arquivo (sem o ponto)
        """
        return "json"