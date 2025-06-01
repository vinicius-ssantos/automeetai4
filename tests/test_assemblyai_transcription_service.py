import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile

from src.services.assemblyai_transcription_service import AssemblyAITranscriptionService
from src.interfaces.config_provider import ConfigProvider
from src.models.transcription_result import TranscriptionResult


class TestAssemblyAITranscriptionService(unittest.TestCase):
    """
    Testes para o AssemblyAITranscriptionService.

    Esta classe de teste verifica se o AssemblyAITranscriptionService transcreve
    corretamente arquivos de áudio usando a API da AssemblyAI.
    """

    def setUp(self):
        """Configuração para cada teste."""
        # Criar um mock para o ConfigProvider
        self.config_provider = Mock(spec=ConfigProvider)

        # Configurar valores padrão para o mock
        self.config_provider.get.return_value = "test_api_key_12345678901234567890"

        # Patch para o validate_api_key para evitar erros de validação
        patcher = patch.object(AssemblyAITranscriptionService, '_validate_api_key')
        self.mock_validate_api_key = patcher.start()
        self.addCleanup(patcher.stop)

        # Criar o serviço com o mock do ConfigProvider
        self.service = AssemblyAITranscriptionService(self.config_provider)

        # Criar diretório temporário para testes
        self.temp_dir = tempfile.mkdtemp()

        # Caminho de arquivo para testes
        self.audio_file = os.path.join(self.temp_dir, "test_audio.mp3")

    def tearDown(self):
        """Limpeza após os testes."""
        # Remover diretório temporário
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('src.services.assemblyai_transcription_service.validate_file_path')
    @patch('src.services.assemblyai_transcription_service.RateLimiterRegistry')
    @patch('src.services.assemblyai_transcription_service.aai')
    @patch('src.services.assemblyai_transcription_service.AssemblyAIAdapter')
    def test_transcribe_success(self, mock_adapter, mock_aai, mock_rate_limiter_registry, mock_validate):
        """Testa a transcrição bem-sucedida de um arquivo de áudio."""
        # Configurar mocks
        mock_rate_limiter = Mock()
        mock_rate_limiter_registry.return_value.get_limiter.return_value = mock_rate_limiter

        mock_transcriber = Mock()
        mock_aai.Transcriber.return_value = mock_transcriber

        mock_transcript = Mock()
        mock_transcriber.transcribe.return_value = mock_transcript

        mock_result = Mock(spec=TranscriptionResult)
        mock_adapter.convert.return_value = mock_result

        # Chamar o método transcribe
        result = self.service.transcribe(
            audio_file=self.audio_file
        )

        # Verificar se o resultado é o esperado
        self.assertEqual(result, mock_result)

        # Verificar se os métodos foram chamados corretamente
        mock_validate.assert_called_once()
        mock_rate_limiter.consume.assert_called_once_with(wait=True)
        mock_transcriber.transcribe.assert_called_once()
        mock_adapter.convert.assert_called_once_with(mock_transcript, self.audio_file)

    @patch('src.services.assemblyai_transcription_service.validate_file_path')
    @patch('src.services.assemblyai_transcription_service.RateLimiterRegistry')
    @patch('src.services.assemblyai_transcription_service.aai')
    @patch('src.adapters.assemblyai_adapter.AssemblyAIAdapter.convert')
    def test_transcribe_with_custom_config(self, mock_convert, mock_aai, mock_rate_limiter_registry, mock_validate):
        """Testa a transcrição com configurações personalizadas."""
        # Configurar mocks
        mock_rate_limiter = Mock()
        mock_rate_limiter_registry.return_value.get_limiter.return_value = mock_rate_limiter

        mock_transcriber = Mock()
        mock_aai.Transcriber.return_value = mock_transcriber

        # Configurar mock para retornar um resultado de transcrição
        mock_transcript = Mock()
        mock_transcript.utterances = []
        mock_transcript.text = "Test transcript"
        mock_transcriber.transcribe.return_value = mock_transcript

        # Configurar mock para o convert
        mock_result = Mock()
        mock_convert.return_value = mock_result

        # Chamar o método transcribe com configurações personalizadas
        result = self.service.transcribe(
            audio_file=self.audio_file,
            config={
                "speaker_labels": True,
                "speakers_expected": 3,
                "language_code": "pt"
            }
        )

        # Verificar se o resultado é o esperado
        self.assertEqual(result, mock_result)

        # Verificar se o TranscriptionConfig foi criado com os parâmetros corretos
        mock_aai.TranscriptionConfig.assert_called_once_with(
            speaker_labels=True,
            speakers_expected=3,
            language_code="pt"
        )

        # Verificar se o convert foi chamado com os parâmetros corretos
        mock_convert.assert_called_once_with(mock_transcript, self.audio_file)

    @patch('src.services.assemblyai_transcription_service.validate_file_path')
    def test_transcribe_file_not_found(self, mock_validate):
        """Testa o comportamento quando o arquivo de áudio não é encontrado."""
        # Configurar mock para lançar FileNotFoundError
        mock_validate.side_effect = FileNotFoundError("File not found")

        # Chamar o método transcribe
        result = self.service.transcribe(
            audio_file=self.audio_file
        )

        # Verificar se o resultado é None (falha)
        self.assertIsNone(result)

    @patch('src.services.assemblyai_transcription_service.validate_file_path')
    @patch('src.services.assemblyai_transcription_service.RateLimiterRegistry')
    @patch('src.services.assemblyai_transcription_service.aai')
    @patch('src.adapters.assemblyai_adapter.AssemblyAIAdapter.convert', return_value=None)
    def test_transcribe_authentication_error(self, mock_convert, mock_aai, mock_rate_limiter_registry, mock_validate):
        """Testa o comportamento quando ocorre um erro de autenticação."""
        # Configurar mocks
        mock_rate_limiter = Mock()
        mock_rate_limiter_registry.return_value.get_limiter.return_value = mock_rate_limiter

        mock_transcriber = Mock()
        mock_aai.Transcriber.return_value = mock_transcriber

        # Criar uma classe de exceção personalizada
        class AuthenticationError(Exception):
            pass

        # Configurar mock para lançar AuthenticationError
        mock_aai.exceptions.AuthenticationError = AuthenticationError
        mock_transcriber.transcribe.side_effect = AuthenticationError("Invalid API key")

        # Chamar o método transcribe
        result = self.service.transcribe(
            audio_file=self.audio_file
        )

        # Verificar se o resultado é None (falha)
        self.assertIsNone(result)

    @patch('src.services.assemblyai_transcription_service.validate_file_path')
    @patch('src.services.assemblyai_transcription_service.RateLimiterRegistry')
    @patch('src.services.assemblyai_transcription_service.aai')
    @patch('src.adapters.assemblyai_adapter.AssemblyAIAdapter.convert', return_value=None)
    def test_transcribe_rate_limit_error(self, mock_convert, mock_aai, mock_rate_limiter_registry, mock_validate):
        """Testa o comportamento quando ocorre um erro de limite de taxa."""
        # Configurar mocks
        mock_rate_limiter = Mock()
        mock_rate_limiter_registry.return_value.get_limiter.return_value = mock_rate_limiter

        mock_transcriber = Mock()
        mock_aai.Transcriber.return_value = mock_transcriber

        # Criar uma classe de exceção personalizada
        class RateLimitError(Exception):
            pass

        # Configurar mock para lançar RateLimitError
        mock_aai.exceptions.RateLimitError = RateLimitError
        mock_transcriber.transcribe.side_effect = RateLimitError("Rate limit exceeded")

        # Chamar o método transcribe
        result = self.service.transcribe(
            audio_file=self.audio_file
        )

        # Verificar se o resultado é None (falha)
        self.assertIsNone(result)

    @patch('src.services.assemblyai_transcription_service.validate_file_path')
    @patch('src.services.assemblyai_transcription_service.RateLimiterRegistry')
    @patch('src.services.assemblyai_transcription_service.aai')
    def test_transcribe_general_exception(self, mock_aai, mock_rate_limiter_registry, mock_validate):
        """Testa o comportamento quando ocorre uma exceção genérica."""
        # Configurar mocks
        mock_rate_limiter = Mock()
        mock_rate_limiter_registry.return_value.get_limiter.return_value = mock_rate_limiter

        mock_transcriber = Mock()
        mock_aai.Transcriber.return_value = mock_transcriber

        # Configurar mock para lançar Exception
        mock_transcriber.transcribe.side_effect = Exception("General error")

        # Chamar o método transcribe
        result = self.service.transcribe(
            audio_file=self.audio_file
        )

        # Verificar se o resultado é None (falha)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
