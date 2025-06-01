"""
Utilitário para validação de valores de configuração.
"""
from typing import Any, Dict, Optional, List, Union, Callable
import os
from src.utils.logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)


class ConfigValidator:
    """
    Classe utilitária para validação de valores de configuração.
    """

    @staticmethod
    def validate_api_key(key: Optional[str], name: str) -> Optional[str]:
        """
        Valida uma chave de API.

        Args:
            key: A chave de API a ser validada
            name: O nome da chave de API (para mensagens de erro)

        Returns:
            Optional[str]: A chave de API validada ou None se inválida

        Raises:
            ValueError: Se a chave de API for inválida
        """
        if not key:
            raise ValueError(f"{name} API key is required.")

        if not isinstance(key, str):
            raise ValueError(f"{name} API key must be a string.")

        if len(key.strip()) < 10:  # Validação básica para o comprimento da chave
            raise ValueError(f"{name} API key appears to be invalid. Please check your API key.")

        return key

    @staticmethod
    def validate_rate_limit(rate: float, name: str) -> float:
        """
        Valida um valor de limite de taxa.

        Args:
            rate: O valor de limite de taxa a ser validado
            name: O nome do limite de taxa (para mensagens de erro)

        Returns:
            float: O valor de limite de taxa validado

        Raises:
            ValueError: Se o valor de limite de taxa for inválido
        """
        if not isinstance(rate, (int, float)):
            raise ValueError(f"{name} rate limit must be a number.")

        if rate <= 0:
            raise ValueError(f"{name} rate limit must be greater than 0.")

        return rate

    @staticmethod
    def validate_directory(directory: str, create_if_missing: bool = False) -> str:
        """
        Valida um diretório.

        Args:
            directory: O diretório a ser validado
            create_if_missing: Se True, cria o diretório se não existir

        Returns:
            str: O diretório validado

        Raises:
            ValueError: Se o diretório for inválido
        """
        if not directory:
            raise ValueError("Directory path cannot be empty.")

        if not isinstance(directory, str):
            raise ValueError("Directory path must be a string.")

        # Criar o diretório se não existir e create_if_missing for True
        if create_if_missing and not os.path.exists(directory):
            try:
                os.makedirs(directory)
                logger.info(f"Created directory: {directory}")
            except OSError as e:
                raise ValueError(f"Failed to create directory {directory}: {e}")

        # Verificar se o diretório existe
        if not os.path.exists(directory):
            raise ValueError(f"Directory {directory} does not exist.")

        # Verificar se é realmente um diretório
        if not os.path.isdir(directory):
            raise ValueError(f"{directory} is not a directory.")

        # Verificar permissões
        if not os.access(directory, os.W_OK):
            raise ValueError(f"No write permission for directory {directory}.")

        return directory

    @staticmethod
    def validate_language_code(code: str) -> str:
        """
        Valida um código de idioma.

        Args:
            code: O código de idioma a ser validado

        Returns:
            str: O código de idioma validado

        Raises:
            ValueError: Se o código de idioma for inválido
        """
        if not isinstance(code, str):
            raise ValueError("Language code must be a string.")

        # Lista de códigos de idioma válidos (simplificada)
        valid_codes = ["pt", "en", "es", "fr", "de", "it", "nl", "ja", "ko", "zh", "ru"]
        
        if code.lower() not in valid_codes:
            logger.warning(f"Language code '{code}' may not be supported. Valid codes include: {', '.join(valid_codes)}")

        return code

    @staticmethod
    def validate_speakers_expected(count: int) -> int:
        """
        Valida o número esperado de falantes.

        Args:
            count: O número esperado de falantes a ser validado

        Returns:
            int: O número esperado de falantes validado

        Raises:
            ValueError: Se o número esperado de falantes for inválido
        """
        if not isinstance(count, int):
            raise ValueError("Speakers expected must be an integer.")

        if count < 1:
            raise ValueError("Speakers expected must be at least 1.")

        if count > 10:
            logger.warning(f"A high number of expected speakers ({count}) may reduce transcription accuracy.")

        return count

    @staticmethod
    def validate_model_name(model: str, valid_models: Optional[List[str]] = None) -> str:
        """
        Valida um nome de modelo.

        Args:
            model: O nome do modelo a ser validado
            valid_models: Lista opcional de nomes de modelos válidos

        Returns:
            str: O nome do modelo validado

        Raises:
            ValueError: Se o nome do modelo for inválido
        """
        if not isinstance(model, str):
            raise ValueError("Model name must be a string.")

        if valid_models and model not in valid_models:
            logger.warning(f"Model '{model}' may not be supported. Valid models include: {', '.join(valid_models)}")

        return model

    @staticmethod
    def validate_config(config: Dict[str, Any], validators: Dict[str, Callable]) -> Dict[str, Any]:
        """
        Valida múltiplos valores de configuração.

        Args:
            config: Dicionário de valores de configuração
            validators: Dicionário mapeando chaves de configuração para funções de validação

        Returns:
            Dict[str, Any]: Dicionário de valores de configuração validados
        """
        validated_config = {}
        
        for key, validator in validators.items():
            if key in config:
                try:
                    validated_config[key] = validator(config[key])
                except ValueError as e:
                    logger.warning(f"Invalid configuration value for {key}: {e}")
                    # Manter o valor original se a validação falhar
                    validated_config[key] = config[key]
            else:
                # Chave não encontrada no config
                logger.debug(f"Configuration key {key} not found.")
        
        return validated_config