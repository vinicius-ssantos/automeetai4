import html
from typing import Dict, Any, Optional

from src.interfaces.output_formatter import OutputFormatter
from src.models.transcription_result import TranscriptionResult
from src.utils.logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)


class HTMLFormatter(OutputFormatter):
    """
    Formatador de saída para HTML.
    Implementa a interface OutputFormatter para formatar resultados de transcrição como HTML.
    """
    
    def format(self, transcription: TranscriptionResult, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Formata um resultado de transcrição como HTML.
        
        Args:
            transcription: O resultado da transcrição a ser formatado
            options: Opções de formatação (opcional)
                - title: Título da página HTML (padrão: "Transcrição")
                - include_timestamps: Se True, inclui timestamps no início de cada fala (padrão: True)
                - include_metadata: Se True, inclui metadados como o arquivo de áudio (padrão: True)
                - css_class_prefix: Prefixo para as classes CSS (padrão: "transcription")
                - speaker_colors: Dicionário mapeando falantes para cores CSS (padrão: None)
                
        Returns:
            str: O resultado formatado como HTML
        """
        if not transcription or not transcription.utterances:
            logger.warning("Tentativa de formatar uma transcrição vazia ou nula")
            return "<html><body><p>Nenhuma transcrição disponível.</p></body></html>"
            
        # Configurações padrão
        title = "Transcrição"
        include_timestamps = True
        include_metadata = True
        css_class_prefix = "transcription"
        speaker_colors = {}
        
        # Aplicar opções personalizadas, se fornecidas
        if options:
            title = options.get("title", title)
            include_timestamps = options.get("include_timestamps", include_timestamps)
            include_metadata = options.get("include_metadata", include_metadata)
            css_class_prefix = options.get("css_class_prefix", css_class_prefix)
            speaker_colors = options.get("speaker_colors", speaker_colors)
        
        # Escapar o título para evitar injeção de HTML
        title_safe = html.escape(title)
        
        # Iniciar o documento HTML
        result = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{title_safe}</title>",
            "<meta charset=\"utf-8\">",
            "<style>",
            f".{css_class_prefix}-container {{ max-width: 800px; margin: 0 auto; font-family: Arial, sans-serif; }}",
            f".{css_class_prefix}-header {{ margin-bottom: 20px; }}",
            f".{css_class_prefix}-metadata {{ color: #666; font-size: 0.9em; margin-bottom: 20px; }}",
            f".{css_class_prefix}-utterance {{ margin-bottom: 10px; }}",
            f".{css_class_prefix}-speaker {{ font-weight: bold; }}",
            f".{css_class_prefix}-timestamp {{ color: #888; font-size: 0.8em; margin-right: 10px; }}",
            f".{css_class_prefix}-text {{ }}",
        ]
        
        # Adicionar estilos específicos para cada falante, se fornecidos
        for speaker, color in speaker_colors.items():
            speaker_safe = html.escape(speaker).replace(" ", "_")
            result.append(f".{css_class_prefix}-speaker-{speaker_safe} {{ color: {color}; }}")
        
        # Finalizar a seção de estilos e iniciar o corpo
        result.extend([
            "</style>",
            "</head>",
            "<body>",
            f"<div class=\"{css_class_prefix}-container\">",
            f"<div class=\"{css_class_prefix}-header\">",
            f"<h1>{title_safe}</h1>",
            "</div>"
        ])
        
        # Adicionar metadados, se solicitado
        if include_metadata and transcription.audio_file:
            audio_file_safe = html.escape(transcription.audio_file)
            result.append(f"<div class=\"{css_class_prefix}-metadata\">")
            result.append(f"<p>Arquivo de áudio: {audio_file_safe}</p>")
            result.append("</div>")
        
        # Adicionar as falas
        result.append(f"<div class=\"{css_class_prefix}-content\">")
        
        for utterance in transcription.utterances:
            speaker_safe = html.escape(utterance.speaker)
            speaker_class = f"{css_class_prefix}-speaker-{speaker_safe.replace(' ', '_')}"
            text_safe = html.escape(utterance.text)
            
            result.append(f"<div class=\"{css_class_prefix}-utterance\">")
            
            # Adicionar timestamp, se solicitado
            if include_timestamps and utterance.start is not None:
                minutes = int(utterance.start / 60)
                seconds = int(utterance.start % 60)
                result.append(f"<span class=\"{css_class_prefix}-timestamp\">[{minutes:02d}:{seconds:02d}]</span>")
            
            # Adicionar falante e texto
            result.append(f"<span class=\"{css_class_prefix}-speaker {speaker_class}\">{speaker_safe}:</span> ")
            result.append(f"<span class=\"{css_class_prefix}-text\">{text_safe}</span>")
            result.append("</div>")
        
        # Finalizar o documento HTML
        result.extend([
            "</div>",
            "</div>",
            "</body>",
            "</html>"
        ])
        
        return "\n".join(result)
    
    def get_file_extension(self) -> str:
        """
        Obtém a extensão de arquivo para este formato.
        
        Returns:
            str: A extensão de arquivo (sem o ponto)
        """
        return "html"