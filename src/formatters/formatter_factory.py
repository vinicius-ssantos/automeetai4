from typing import Dict, Type, Optional

from src.interfaces.output_formatter import OutputFormatter
from src.formatters.text_formatter import TextFormatter
from src.formatters.json_formatter import JSONFormatter
from src.formatters.html_formatter import HTMLFormatter
from src.utils.logging import get_logger
from src.exceptions import UnsupportedFormatError

# Initialize logger for this module
logger = get_logger(__name__)


class FormatterFactory:
    """
    Fábrica para criar formatadores de saída.
    Implementa o padrão Factory para criar instâncias de formatadores
    com base no formato solicitado.
    """

    # Mapeamento de nomes de formato para classes de formatador
    _formatters: Dict[str, Type[OutputFormatter]] = {
        "text": TextFormatter,
        "txt": TextFormatter,
        "json": JSONFormatter,
        "html": HTMLFormatter,
        "htm": HTMLFormatter
    }

    @classmethod
    def get_formatter(cls, format_name: str) -> OutputFormatter:
        """
        Obtém um formatador para o formato especificado.

        Args:
            format_name: Nome do formato (text, json, html, etc.)

        Returns:
            OutputFormatter: Uma instância do formatador

        Raises:
            UnsupportedFormatError: Se o formato não for suportado
        """
        # Normalizar o nome do formato
        format_name = format_name.lower().strip()

        # Obter a classe do formatador
        formatter_class = cls._formatters.get(format_name)

        if not formatter_class:
            logger.warning(f"Formato não suportado: {format_name}")
            raise UnsupportedFormatError(f"Formato não suportado: {format_name}")

        # Criar e retornar uma instância do formatador
        return formatter_class()

    @classmethod
    def register_formatter(cls, format_name: str, formatter_class: Type[OutputFormatter]) -> None:
        """
        Registra um novo formatador.

        Args:
            format_name: Nome do formato
            formatter_class: Classe do formatador
        """
        cls._formatters[format_name.lower().strip()] = formatter_class
        logger.info(f"Formatador registrado para o formato: {format_name}")

    @classmethod
    def get_supported_formats(cls) -> list[str]:
        """
        Obtém a lista de formatos suportados.

        Returns:
            list[str]: Lista de nomes de formatos suportados
        """
        return list(cls._formatters.keys())
