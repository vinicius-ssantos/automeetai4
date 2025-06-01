"""
Mock objects for AssemblyAI services.

Este módulo contém implementações de mock para os serviços da AssemblyAI,
permitindo testes sem dependências externas.
"""

from typing import Dict, Any, Optional, List
from unittest.mock import MagicMock

# Import the pydantic patch before any assemblyai imports
from src.patches.pydantic_patch import *


class MockAssemblyAITranscript:
    """
    Mock para o objeto de transcrição da AssemblyAI.

    Esta classe simula o comportamento de um objeto de transcrição retornado
    pela API da AssemblyAI.
    """

    def __init__(self, text: str = "Mock transcript text", status: str = "completed"):
        """
        Inicializa o mock de transcrição.

        Args:
            text: O texto da transcrição
            status: O status da transcrição
        """
        self.text = text
        self.status = status
        self.utterances = []
        self.id = "mock-transcript-id-12345"
        self.audio_url = "https://example.com/audio.mp3"
        self.error = None

    def add_utterance(self, speaker: str, text: str, start: int = 0, end: int = 1000):
        """
        Adiciona uma fala à transcrição.

        Args:
            speaker: O identificador do falante
            text: O texto falado
            start: O tempo de início em milissegundos
            end: O tempo de fim em milissegundos
        """
        self.utterances.append({
            "speaker": speaker,
            "text": text,
            "start": start,
            "end": end
        })
        return self


class MockAssemblyAITranscriber:
    """
    Mock para o transcritor da AssemblyAI.

    Esta classe simula o comportamento do objeto Transcriber da AssemblyAI.
    """

    def __init__(self, should_fail: bool = False, error_type: Optional[str] = None):
        """
        Inicializa o mock do transcritor.

        Args:
            should_fail: Indica se a transcrição deve falhar
            error_type: O tipo de erro a ser simulado
        """
        self.should_fail = should_fail
        self.error_type = error_type
        self.transcripts = {}

    def transcribe(self, audio_file: str, config: Any = None) -> MockAssemblyAITranscript:
        """
        Simula a transcrição de um arquivo de áudio.

        Args:
            audio_file: O caminho para o arquivo de áudio
            config: Configuração opcional para a transcrição

        Returns:
            MockAssemblyAITranscript: Um objeto de transcrição simulado

        Raises:
            Exception: Se should_fail for True, lança uma exceção do tipo especificado
        """
        import assemblyai as aai

        if self.should_fail:
            if self.error_type == "auth":
                raise aai.exceptions.AuthenticationError("Invalid API key")
            elif self.error_type == "rate_limit":
                raise aai.exceptions.RateLimitError("Rate limit exceeded")
            elif self.error_type == "timeout":
                raise aai.exceptions.RequestTimeoutError("Request timed out")
            elif self.error_type == "api":
                raise aai.exceptions.APIError("API error")
            else:
                raise Exception("Generic transcription error")

        # Criar uma transcrição simulada com base no arquivo e configuração
        transcript = MockAssemblyAITranscript()

        # Adicionar algumas falas simuladas
        transcript.add_utterance("A", "Hello, this is speaker A.")
        transcript.add_utterance("B", "Hi, this is speaker B.")

        # Armazenar a transcrição para referência futura
        self.transcripts[audio_file] = transcript

        return transcript


class MockAssemblyAISettings:
    """
    Mock para as configurações da AssemblyAI.

    Esta classe simula o objeto de configurações da AssemblyAI.
    """

    def __init__(self):
        """Inicializa o mock de configurações."""
        self.api_key = None


class MockAssemblyAITranscriptionConfig:
    """
    Mock para a configuração de transcrição da AssemblyAI.

    Esta classe simula o objeto TranscriptionConfig da AssemblyAI.
    """

    def __init__(self, speaker_labels: bool = False, speakers_expected: int = 2, language_code: str = "en"):
        """
        Inicializa o mock de configuração de transcrição.

        Args:
            speaker_labels: Indica se a detecção de falantes está ativada
            speakers_expected: O número esperado de falantes
            language_code: O código do idioma para a transcrição
        """
        self.speaker_labels = speaker_labels
        self.speakers_expected = speakers_expected
        self.language_code = language_code


class MockAssemblyAI:
    """
    Mock para o módulo AssemblyAI.

    Esta classe simula o comportamento do módulo AssemblyAI, fornecendo
    acesso a objetos simulados para testes.
    """

    def __init__(self):
        """Inicializa o mock do módulo AssemblyAI."""
        self.settings = MockAssemblyAISettings()
        self.exceptions = MagicMock()
        self.exceptions.AuthenticationError = type('AuthenticationError', (Exception,), {})
        self.exceptions.RateLimitError = type('RateLimitError', (Exception,), {})
        self.exceptions.RequestTimeoutError = type('RequestTimeoutError', (Exception,), {})
        self.exceptions.APIError = type('APIError', (Exception,), {})

    def Transcriber(self):
        """
        Cria um novo transcritor simulado.

        Returns:
            MockAssemblyAITranscriber: Um transcritor simulado
        """
        return MockAssemblyAITranscriber()

    def TranscriptionConfig(self, **kwargs):
        """
        Cria uma nova configuração de transcrição simulada.

        Args:
            **kwargs: Parâmetros para a configuração

        Returns:
            MockAssemblyAITranscriptionConfig: Uma configuração simulada
        """
        return MockAssemblyAITranscriptionConfig(**kwargs)


def create_mock_assemblyai():
    """
    Cria um mock completo do módulo AssemblyAI.

    Returns:
        MockAssemblyAI: Um mock do módulo AssemblyAI
    """
    return MockAssemblyAI()
