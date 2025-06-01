"""
Service fixtures for testing.

Este módulo contém fixtures relacionados a serviços para uso em testes.
"""

from typing import Dict, Any, Optional, List, Callable, Generator, Tuple
from unittest.mock import Mock

from src.interfaces.config_provider import ConfigProvider
from src.interfaces.audio_converter import AudioConverter
from src.interfaces.transcription_service import TranscriptionService
from src.interfaces.text_generation_service import TextGenerationService
from src.models.transcription_result import TranscriptionResult

from tests.mocks.assemblyai_mocks import create_mock_assemblyai, MockAssemblyAITranscript
from tests.mocks.openai_mocks import create_mock_openai
from tests.mocks.moviepy_mocks import create_mock_moviepy


def mock_config_provider(config_values: Optional[Dict[str, Any]] = None) -> ConfigProvider:
    """
    Cria um mock do ConfigProvider.
    
    Args:
        config_values: Dicionário de valores de configuração
        
    Returns:
        ConfigProvider: Um mock do ConfigProvider
        
    Example:
        ```python
        def test_something():
            config = mock_config_provider({
                "output_directory": "test_output",
                "openai_api_key": "test_key"
            })
            # Use config para testes
            assert config.get("output_directory") == "test_output"
        ```
    """
    config_values = config_values or {}
    
    mock_config = Mock(spec=ConfigProvider)
    mock_config.get.side_effect = lambda key, default=None: config_values.get(key, default)
    
    return mock_config


def mock_audio_converter(should_fail: bool = False, error_type: Optional[str] = None) -> AudioConverter:
    """
    Cria um mock do AudioConverter.
    
    Args:
        should_fail: Indica se a conversão deve falhar
        error_type: O tipo de erro a ser simulado
        
    Returns:
        AudioConverter: Um mock do AudioConverter
        
    Example:
        ```python
        def test_something():
            converter = mock_audio_converter()
            # Use converter para testes
            assert converter.convert("input.mp4", "output.mp3")
        ```
    """
    mock_converter = Mock(spec=AudioConverter)
    
    if should_fail:
        mock_converter.convert.return_value = False
    else:
        mock_converter.convert.return_value = True
    
    return mock_converter


def mock_transcription_service(
    should_fail: bool = False,
    error_type: Optional[str] = None,
    transcript_text: Optional[str] = None,
    utterances: Optional[List[Dict[str, Any]]] = None
) -> TranscriptionService:
    """
    Cria um mock do TranscriptionService.
    
    Args:
        should_fail: Indica se a transcrição deve falhar
        error_type: O tipo de erro a ser simulado
        transcript_text: O texto da transcrição
        utterances: Lista de falas para a transcrição
        
    Returns:
        TranscriptionService: Um mock do TranscriptionService
        
    Example:
        ```python
        def test_something():
            service = mock_transcription_service(
                transcript_text="Hello world",
                utterances=[
                    {"speaker": "A", "text": "Hello"},
                    {"speaker": "B", "text": "world"}
                ]
            )
            # Use service para testes
            result = service.transcribe("audio.mp3")
            assert result is not None
        ```
    """
    mock_service = Mock(spec=TranscriptionService)
    
    if should_fail:
        mock_service.transcribe.return_value = None
    else:
        # Criar um mock de transcrição
        mock_transcript = {}
        
        if transcript_text:
            mock_transcript["text"] = transcript_text
        
        if utterances:
            mock_transcript["utterances"] = utterances
        else:
            mock_transcript["utterances"] = [
                {"speaker": "A", "text": "Hello, this is a test."},
                {"speaker": "B", "text": "Yes, it is a test."}
            ]
        
        mock_service.transcribe.return_value = mock_transcript
    
    return mock_service


def mock_text_generation_service(
    should_fail: bool = False,
    error_type: Optional[str] = None,
    generated_text: str = "Mock generated text"
) -> TextGenerationService:
    """
    Cria um mock do TextGenerationService.
    
    Args:
        should_fail: Indica se a geração deve falhar
        error_type: O tipo de erro a ser simulado
        generated_text: O texto gerado
        
    Returns:
        TextGenerationService: Um mock do TextGenerationService
        
    Example:
        ```python
        def test_something():
            service = mock_text_generation_service(
                generated_text="This is a summary of the meeting."
            )
            # Use service para testes
            result = service.generate("system prompt", "user prompt")
            assert result == "This is a summary of the meeting."
        ```
    """
    mock_service = Mock(spec=TextGenerationService)
    
    if should_fail:
        mock_service.generate.return_value = ""
    else:
        mock_service.generate.return_value = generated_text
    
    return mock_service


def mock_transcription_result(
    audio_file: str = "test_audio.mp3",
    utterances: Optional[List[Dict[str, Any]]] = None
) -> TranscriptionResult:
    """
    Cria um mock do TranscriptionResult.
    
    Args:
        audio_file: O caminho para o arquivo de áudio
        utterances: Lista de falas para a transcrição
        
    Returns:
        TranscriptionResult: Um mock do TranscriptionResult
        
    Example:
        ```python
        def test_something():
            result = mock_transcription_result(
                audio_file="audio.mp3",
                utterances=[
                    {"speaker": "A", "text": "Hello"},
                    {"speaker": "B", "text": "world"}
                ]
            )
            # Use result para testes
            assert result.audio_file == "audio.mp3"
        ```
    """
    if utterances is None:
        utterances = [
            {"speaker": "A", "text": "Hello, this is a test."},
            {"speaker": "B", "text": "Yes, it is a test."}
        ]
    
    mock_result = Mock(spec=TranscriptionResult)
    mock_result.audio_file = audio_file
    mock_result.utterances = utterances
    mock_result.to_formatted_text.return_value = "\n".join([f"Speaker {u['speaker']}: {u['text']}" for u in utterances])
    mock_result.save_to_file.return_value = True
    mock_result.save_as_multiple_formats.return_value = {"txt": True, "json": True}
    
    return mock_result


class ServiceFixtures:
    """
    Conjunto de fixtures para serviços.
    
    Esta classe fornece métodos para criar e configurar mocks de serviços
    para uso em testes.
    """
    
    @staticmethod
    def create_all_mocks(
        config_values: Optional[Dict[str, Any]] = None,
        audio_converter_should_fail: bool = False,
        transcription_service_should_fail: bool = False,
        text_generation_service_should_fail: bool = False
    ) -> Tuple[ConfigProvider, AudioConverter, TranscriptionService, TextGenerationService]:
        """
        Cria mocks para todos os serviços principais.
        
        Args:
            config_values: Valores de configuração para o ConfigProvider
            audio_converter_should_fail: Indica se o AudioConverter deve falhar
            transcription_service_should_fail: Indica se o TranscriptionService deve falhar
            text_generation_service_should_fail: Indica se o TextGenerationService deve falhar
            
        Returns:
            Tuple: Uma tupla contendo mocks para ConfigProvider, AudioConverter,
                  TranscriptionService e TextGenerationService
                  
        Example:
            ```python
            def test_something():
                config, converter, transcription, text_gen = ServiceFixtures.create_all_mocks()
                # Use os mocks para testes
                app = AutoMeetAI(config, converter, transcription, text_gen)
                # ...
            ```
        """
        config = mock_config_provider(config_values)
        converter = mock_audio_converter(should_fail=audio_converter_should_fail)
        transcription = mock_transcription_service(should_fail=transcription_service_should_fail)
        text_gen = mock_text_generation_service(should_fail=text_generation_service_should_fail)
        
        return config, converter, transcription, text_gen