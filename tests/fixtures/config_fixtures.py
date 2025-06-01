"""
Configuration fixtures for testing.

Este módulo contém fixtures relacionados a configurações para uso em testes.
"""

import os
from typing import Dict, Any, Optional, List, Callable, Generator, Tuple

from src.config.env_config_provider import EnvConfigProvider


def with_env_vars(env_vars: Dict[str, str]) -> Generator[Dict[str, str], None, None]:
    """
    Configura variáveis de ambiente temporárias para testes.
    
    Args:
        env_vars: Dicionário de variáveis de ambiente para configurar
        
    Yields:
        Dict[str, str]: O dicionário de variáveis de ambiente originais
        
    Example:
        ```python
        def test_something():
            with with_env_vars({
                "AUTOMEETAI_OPENAI_API_KEY": "test_key",
                "AUTOMEETAI_OUTPUT_DIRECTORY": "test_output"
            }):
                # Código que usa as variáveis de ambiente
                config = EnvConfigProvider()
                assert config.get("openai_api_key") == "test_key"
        ```
    """
    # Salvar as variáveis de ambiente originais
    original_env = {}
    for key in env_vars:
        if key in os.environ:
            original_env[key] = os.environ[key]
        else:
            original_env[key] = None
    
    # Configurar as novas variáveis de ambiente
    for key, value in env_vars.items():
        os.environ[key] = value
    
    try:
        yield original_env
    finally:
        # Restaurar as variáveis de ambiente originais
        for key, value in original_env.items():
            if value is None:
                if key in os.environ:
                    del os.environ[key]
            else:
                os.environ[key] = value


def create_env_config_provider(env_vars: Dict[str, str]) -> EnvConfigProvider:
    """
    Cria um EnvConfigProvider com variáveis de ambiente específicas.
    
    Args:
        env_vars: Dicionário de variáveis de ambiente para configurar
        
    Returns:
        EnvConfigProvider: Um provedor de configuração baseado em variáveis de ambiente
        
    Example:
        ```python
        def test_something():
            config = create_env_config_provider({
                "AUTOMEETAI_OPENAI_API_KEY": "test_key",
                "AUTOMEETAI_OUTPUT_DIRECTORY": "test_output"
            })
            # Use config para testes
            assert config.get("openai_api_key") == "test_key"
        ```
    """
    # Configurar as variáveis de ambiente
    for key, value in env_vars.items():
        os.environ[key] = value
    
    # Criar o provedor de configuração
    return EnvConfigProvider()


class TestConfigBuilder:
    """
    Construtor de configurações para testes.
    
    Esta classe facilita a criação de configurações para testes usando
    o padrão Builder.
    """
    
    def __init__(self):
        """
        Inicializa o construtor de configurações.
        """
        self.config = {}
    
    def with_api_keys(self, assemblyai_key: str = "test_assemblyai_key", openai_key: str = "test_openai_key") -> 'TestConfigBuilder':
        """
        Adiciona chaves de API à configuração.
        
        Args:
            assemblyai_key: Chave de API da AssemblyAI
            openai_key: Chave de API da OpenAI
            
        Returns:
            TestConfigBuilder: O próprio construtor para encadeamento
        """
        self.config["assemblyai_api_key"] = assemblyai_key
        self.config["openai_api_key"] = openai_key
        return self
    
    def with_output_directory(self, output_directory: str = "test_output") -> 'TestConfigBuilder':
        """
        Adiciona diretório de saída à configuração.
        
        Args:
            output_directory: Diretório de saída
            
        Returns:
            TestConfigBuilder: O próprio construtor para encadeamento
        """
        self.config["output_directory"] = output_directory
        return self
    
    def with_audio_settings(self, bitrate: str = "128k", fps: int = 44100) -> 'TestConfigBuilder':
        """
        Adiciona configurações de áudio à configuração.
        
        Args:
            bitrate: Taxa de bits para conversão de áudio
            fps: Taxa de amostragem para conversão de áudio
            
        Returns:
            TestConfigBuilder: O próprio construtor para encadeamento
        """
        self.config["audio_bitrate"] = bitrate
        self.config["audio_fps"] = fps
        return self
    
    def with_transcription_settings(
        self,
        speaker_labels: bool = True,
        speakers_expected: int = 2,
        language_code: str = "pt"
    ) -> 'TestConfigBuilder':
        """
        Adiciona configurações de transcrição à configuração.
        
        Args:
            speaker_labels: Indica se a detecção de falantes está ativada
            speakers_expected: O número esperado de falantes
            language_code: O código do idioma para a transcrição
            
        Returns:
            TestConfigBuilder: O próprio construtor para encadeamento
        """
        self.config["speaker_labels"] = speaker_labels
        self.config["speakers_expected"] = speakers_expected
        self.config["language_code"] = language_code
        return self
    
    def with_openai_settings(self, model: str = "gpt-3.5-turbo", temperature: float = 0.7) -> 'TestConfigBuilder':
        """
        Adiciona configurações da OpenAI à configuração.
        
        Args:
            model: O modelo a ser usado
            temperature: A temperatura para a geração
            
        Returns:
            TestConfigBuilder: O próprio construtor para encadeamento
        """
        self.config["openai_model"] = model
        self.config["temperature"] = temperature
        return self
    
    def with_custom_setting(self, key: str, value: Any) -> 'TestConfigBuilder':
        """
        Adiciona uma configuração personalizada à configuração.
        
        Args:
            key: A chave da configuração
            value: O valor da configuração
            
        Returns:
            TestConfigBuilder: O próprio construtor para encadeamento
        """
        self.config[key] = value
        return self
    
    def build(self) -> Dict[str, Any]:
        """
        Constrói a configuração.
        
        Returns:
            Dict[str, Any]: A configuração construída
        """
        return self.config.copy()
    
    def build_env_vars(self) -> Dict[str, str]:
        """
        Constrói um dicionário de variáveis de ambiente a partir da configuração.
        
        Returns:
            Dict[str, str]: Dicionário de variáveis de ambiente
        """
        env_vars = {}
        
        # Mapear configurações para variáveis de ambiente
        mapping = {
            "assemblyai_api_key": "AUTOMEETAI_ASSEMBLYAI_API_KEY",
            "openai_api_key": "AUTOMEETAI_OPENAI_API_KEY",
            "output_directory": "AUTOMEETAI_OUTPUT_DIRECTORY",
            "audio_bitrate": "AUTOMEETAI_AUDIO_BITRATE",
            "audio_fps": "AUTOMEETAI_AUDIO_FPS",
            "speaker_labels": "AUTOMEETAI_SPEAKER_LABELS",
            "speakers_expected": "AUTOMEETAI_SPEAKERS_EXPECTED",
            "language_code": "AUTOMEETAI_LANGUAGE_CODE",
            "openai_model": "AUTOMEETAI_OPENAI_MODEL",
            "temperature": "AUTOMEETAI_TEMPERATURE"
        }
        
        for key, env_key in mapping.items():
            if key in self.config:
                env_vars[env_key] = str(self.config[key])
        
        return env_vars
    
    def build_env_config_provider(self) -> EnvConfigProvider:
        """
        Constrói um EnvConfigProvider a partir da configuração.
        
        Returns:
            EnvConfigProvider: Um provedor de configuração baseado em variáveis de ambiente
        """
        env_vars = self.build_env_vars()
        return create_env_config_provider(env_vars)


def default_test_config() -> Dict[str, Any]:
    """
    Cria uma configuração padrão para testes.
    
    Returns:
        Dict[str, Any]: Uma configuração padrão para testes
        
    Example:
        ```python
        def test_something():
            config = default_test_config()
            # Use config para testes
            assert "output_directory" in config
        ```
    """
    return TestConfigBuilder() \
        .with_api_keys() \
        .with_output_directory() \
        .with_audio_settings() \
        .with_transcription_settings() \
        .with_openai_settings() \
        .build()