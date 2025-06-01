from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import os
from src.utils.logging import get_logger
from src.exceptions import UnsupportedFormatError, FormattingFailedError, FileError

# Initialize logger for this module
logger = get_logger(__name__)


@dataclass
class Speaker:
    """
    Representa um falante em uma transcrição.
    """
    id: str
    name: str


@dataclass
class Utterance:
    """
    Representa uma única fala em uma transcrição.
    """
    speaker: str
    text: str
    start: Optional[float] = None
    end: Optional[float] = None


@dataclass
class TranscriptionResult:
    """
    Representa o resultado de uma transcrição.
    """
    utterances: List[Utterance]
    text: str
    audio_file: str
    id: Optional[str] = None
    speakers: Optional[List[Speaker]] = None
    language: Optional[str] = None

    def to_formatted_text(self) -> str:
        """
        Convert the transcription result to a formatted text string.

        Returns:
            str: The formatted transcription text
        """
        result = []
        for utterance in self.utterances:
            result.append(f"{utterance.speaker}: {utterance.text}")

        return "\n".join(result)

    def format(self, format_name: str, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Formata o resultado da transcrição no formato especificado.

        Args:
            format_name: Nome do formato (text, json, html, etc.)
            options: Opções de formatação específicas para o formatador

        Returns:
            str: O resultado formatado

        Raises:
            UnsupportedFormatError: Se o formato não for suportado
            FormattingFailedError: Se ocorrer um erro durante a formatação
        """
        # Importar aqui para evitar importação circular
        from src.formatters.formatter_factory import FormatterFactory

        try:
            # O método get_formatter agora lança UnsupportedFormatError se o formato não for suportado
            formatter = FormatterFactory.get_formatter(format_name)
            return formatter.format(self, options)
        except UnsupportedFormatError:
            # Repassar a exceção UnsupportedFormatError
            logger.error(f"Formato não suportado: {format_name}")
            raise
        except Exception as e:
            # Converter outras exceções em FormattingFailedError
            logger.error(f"Erro ao formatar transcrição como {format_name}: {e}")
            raise FormattingFailedError(f"Erro ao formatar transcrição como {format_name}: {e}") from e

    def save_to_file(self, output_file: str, format_name: Optional[str] = None, 
                    options: Optional[Dict[str, Any]] = None) -> bool:
        """
        Salva o resultado da transcrição em um arquivo.

        Args:
            output_file: Caminho onde a transcrição deve ser salva
            format_name: Nome do formato (text, json, html, etc.). Se None, será inferido da extensão do arquivo
            options: Opções de formatação específicas para o formatador

        Returns:
            bool: True se o arquivo foi salvo com sucesso, False caso contrário

        Raises:
            UnsupportedFormatError: Se o formato não for suportado
            FormattingFailedError: Se ocorrer um erro durante a formatação
            FileError: Se ocorrer um erro ao salvar o arquivo
        """
        try:
            # Se o formato não foi especificado, inferir da extensão do arquivo
            if not format_name:
                _, ext = os.path.splitext(output_file)
                if ext:
                    format_name = ext[1:]  # Remover o ponto
                else:
                    format_name = "txt"  # Formato padrão

            # Formatar o conteúdo - pode lançar UnsupportedFormatError ou FormattingFailedError
            content = self.format(format_name, options)

            # Salvar no arquivo
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            except PermissionError as e:
                raise FileError(f"Erro de permissão ao salvar arquivo {output_file}: {e}") from e
            except OSError as e:
                raise FileError(f"Erro ao salvar arquivo {output_file}: {e}") from e

            logger.info(f"Transcrição salva em {output_file}")
            return True

        except (UnsupportedFormatError, FormattingFailedError, FileError):
            # Repassar exceções personalizadas
            raise
        except Exception as e:
            # Converter outras exceções em FileError
            logger.error(f"Erro inesperado ao salvar transcrição no arquivo: {e}")
            raise FileError(f"Erro inesperado ao salvar transcrição no arquivo: {e}") from e

    def save_as_multiple_formats(self, base_output_file: str, formats: List[str], 
                               options: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, bool]:
        """
        Salva o resultado da transcrição em múltiplos formatos.

        Args:
            base_output_file: Caminho base para os arquivos de saída (sem extensão)
            formats: Lista de formatos para salvar
            options: Dicionário mapeando formatos para suas opções específicas

        Returns:
            Dict[str, bool]: Dicionário mapeando formatos para status de sucesso
        """
        results = {}

        for format_name in formats:
            try:
                # Importar aqui para evitar importação circular
                from src.formatters.formatter_factory import FormatterFactory

                # Obter o formatador - pode lançar UnsupportedFormatError
                formatter = FormatterFactory.get_formatter(format_name)

                # Obter a extensão do arquivo para este formato
                extension = formatter.get_file_extension()
                output_file = f"{base_output_file}.{extension}"

                # Obter opções específicas para este formato, se fornecidas
                format_options = None
                if options and format_name in options:
                    format_options = options[format_name]

                # Salvar no formato - pode lançar várias exceções
                try:
                    self.save_to_file(output_file, format_name, format_options)
                    results[format_name] = True
                except Exception as e:
                    logger.error(f"Erro ao salvar no formato {format_name}: {e}")
                    results[format_name] = False

            except Exception as e:
                logger.error(f"Erro ao processar formato {format_name}: {e}")
                results[format_name] = False

        return results
