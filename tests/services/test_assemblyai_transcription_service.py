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

        # Create a mock transcriber
        self.mock_transcriber = Mock()

        # Criar o serviço com o mock do ConfigProvider e o mock do transcriber
        self.service = AssemblyAITranscriptionService(self.config_provider, self.mock_transcriber)

        # Criar diretório temporário para testes
        self.temp_dir = tempfile.mkdtemp()

        # Caminho de arquivo para testes
        self.audio_file = os.path.join(self.temp_dir, "test_audio.mp3")

        # Create an empty audio file for testing
        with open(self.audio_file, 'wb') as f:
            f.write(b'\x00' * 1024)  # Write 1KB of zeros to simulate an audio file

    def tearDown(self):
        """Limpeza após os testes."""
        # Remover diretório temporário
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('src.services.assemblyai_transcription_service.validate_file_path')
    @patch('src.services.assemblyai_transcription_service.RateLimiterRegistry')
    @patch('src.services.assemblyai_transcription_service.aai')
    @patch('src.adapters.assemblyai_adapter.AssemblyAIAdapter.convert')
    @patch('src.services.assemblyai_transcription_service.os.path.exists')
    def test_transcribe_success(self, mock_exists, mock_convert, mock_aai, mock_rate_limiter_registry, mock_validate):
        """Testa a transcrição bem-sucedida de um arquivo de áudio."""
        # Configurar mocks
        mock_rate_limiter = Mock()
        mock_rate_limiter_registry.return_value.get_limiter.return_value = mock_rate_limiter

        # Create a mock transcript with the necessary attributes
        mock_transcript = Mock()
        mock_transcript.utterances = []
        mock_transcript.text = "Test transcript"
        self.mock_transcriber.transcribe.return_value = mock_transcript

        # Create a mock result for the adapter to return
        mock_result = Mock(spec=TranscriptionResult)
        mock_convert.return_value = mock_result

        # Ensure validate_file_path returns True (valid file path)
        mock_validate.return_value = True

        # Ensure os.path.exists returns True for the audio file
        mock_exists.return_value = True

        # Chamar o método transcribe
        result = self.service.transcribe(
            audio_file=self.audio_file
        )

        # Verificar se o resultado é o esperado
        self.assertEqual(result, mock_result)

        # Verificar se os métodos foram chamados corretamente
        mock_validate.assert_called_once()
        mock_rate_limiter.consume.assert_called_once_with(wait=True)
        self.mock_transcriber.transcribe.assert_called_once()
        mock_convert.assert_called_once_with(mock_transcript, self.audio_file)

    @patch('src.services.assemblyai_transcription_service.validate_file_path')
    @patch('src.services.assemblyai_transcription_service.RateLimiterRegistry')
    @patch('src.services.assemblyai_transcription_service.TranscriptionConfig')
    @patch('src.adapters.assemblyai_adapter.AssemblyAIAdapter.convert')
    @patch('src.services.assemblyai_transcription_service.os.path.exists')
    def test_transcribe_with_custom_config(self, mock_exists, mock_convert, mock_transcription_config, mock_rate_limiter_registry, mock_validate):
        """Testa a transcrição com configurações personalizadas."""
        # Configurar mocks
        mock_rate_limiter = Mock()
        mock_rate_limiter_registry.return_value.get_limiter.return_value = mock_rate_limiter

        # Configurar mock para retornar um resultado de transcrição
        mock_transcript = Mock()
        mock_transcript.utterances = []
        mock_transcript.text = "Test transcript"
        self.mock_transcriber.transcribe.return_value = mock_transcript

        # Configurar mock para o convert
        mock_result = Mock()
        mock_convert.return_value = mock_result

        # Ensure validate_file_path returns True (valid file path)
        mock_validate.return_value = True

        # Ensure os.path.exists returns True for the audio file
        mock_exists.return_value = True

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

        # Verificar se o TranscriptionConfig foi chamado
        self.assertTrue(mock_transcription_config.called)

        # Verificar se os parâmetros principais foram passados corretamente
        # Agora estamos passando um dicionário filtrado para o TranscriptionConfig
        call_args = mock_transcription_config.call_args
        # Verificar se foi chamado com **kwargs (um dicionário)
        self.assertEqual(len(call_args[0]), 0)  # Sem argumentos posicionais
        self.assertTrue(len(call_args[1]) > 0)  # Com argumentos nomeados

        # Verificar os parâmetros principais
        call_kwargs = call_args[1]
        self.assertEqual(call_kwargs["speaker_labels"], True)
        self.assertEqual(call_kwargs["speakers_expected"], 3)
        self.assertEqual(call_kwargs["language_code"], "pt")

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
    @patch('src.adapters.assemblyai_adapter.AssemblyAIAdapter.convert')
    def test_transcribe_general_exception(self, mock_convert, mock_rate_limiter_registry, mock_validate):
        """Testa o comportamento quando ocorre uma exceção genérica."""
        # Configurar mocks
        mock_rate_limiter = Mock()
        mock_rate_limiter_registry.return_value.get_limiter.return_value = mock_rate_limiter

        # Configurar mock para lançar Exception
        self.mock_transcriber.transcribe.side_effect = Exception("General error")

        # Ensure convert returns None for exceptions
        mock_convert.return_value = None

        # Chamar o método transcribe
        result = self.service.transcribe(
            audio_file=self.audio_file
        )

        # Verificar se o resultado é None (falha)
        self.assertIsNone(result)

    @patch('src.services.assemblyai_transcription_service.validate_file_path')
    @patch('src.services.assemblyai_transcription_service.RateLimiterRegistry')
    @patch('src.adapters.assemblyai_adapter.AssemblyAIAdapter.convert')
    @patch('src.services.assemblyai_transcription_service.os.path.exists')
    def test_default_config_no_validation_error(self, mock_exists, mock_convert, mock_rate_limiter_registry, mock_validate):
        """Testa que o DEFAULT_CONFIG não causa ValidationError."""
        # Configurar mocks
        mock_rate_limiter = Mock()
        mock_rate_limiter_registry.return_value.get_limiter.return_value = mock_rate_limiter

        # Create a mock transcript with the necessary attributes
        mock_transcript = Mock()
        mock_transcript.utterances = []
        mock_transcript.text = "Test transcript"
        self.mock_transcriber.transcribe.return_value = mock_transcript

        # Create a mock result for the adapter to return
        mock_result = Mock(spec=TranscriptionResult)
        mock_convert.return_value = mock_result

        # Ensure validate_file_path returns True (valid file path)
        mock_validate.return_value = True

        # Ensure os.path.exists returns True for the audio file
        mock_exists.return_value = True

        # Chamar o método transcribe sem fornecer config (deve usar DEFAULT_CONFIG)
        result = self.service.transcribe(
            audio_file=self.audio_file
        )

        # Verificar se o transcribe foi chamado com o DEFAULT_CONFIG
        self.mock_transcriber.transcribe.assert_called_once()
        call_args = self.mock_transcriber.transcribe.call_args
        self.assertEqual(call_args[1]['config'], self.service.DEFAULT_CONFIG)

    @patch('src.services.assemblyai_transcription_service.validate_file_path')
    @patch('src.services.assemblyai_transcription_service.RateLimiterRegistry')
    @patch('src.services.assemblyai_transcription_service.aai')
    @patch('src.services.assemblyai_transcription_service.TranscriptionConfig')
    @patch('src.adapters.assemblyai_adapter.AssemblyAIAdapter.convert')
    @patch('src.services.assemblyai_transcription_service.os.path.exists')
    def test_language_detection_disabled_when_language_code_provided(self, mock_exists, mock_convert, mock_transcription_config, mock_aai, mock_rate_limiter_registry, mock_validate):
        """Testa se language_detection é desativado quando language_code é fornecido."""
        # Configurar mocks
        mock_rate_limiter = Mock()
        mock_rate_limiter_registry.return_value.get_limiter.return_value = mock_rate_limiter

        # Create a mock transcript with the necessary attributes
        mock_transcript = Mock()
        mock_transcript.utterances = []
        mock_transcript.text = "Test transcript"
        self.mock_transcriber.transcribe.return_value = mock_transcript

        # Create a mock result for the adapter to return
        mock_result = Mock(spec=TranscriptionResult)
        mock_convert.return_value = mock_result

        # Ensure validate_file_path returns True (valid file path)
        mock_validate.return_value = True

        # Ensure os.path.exists returns True for the audio file
        mock_exists.return_value = True

        # Mock para TranscriptionConfig
        mock_config = Mock()
        mock_transcription_config.return_value = mock_config

        # Chamar o método transcribe com language_code explícito
        result = self.service.transcribe(
            audio_file=self.audio_file,
            config={
                "language_code": "en"
            }
        )

        # Verificar se o resultado é o esperado
        self.assertEqual(result, mock_result)

        # Verificar se TranscriptionConfig foi chamado com language_detection=False
        call_args = mock_transcription_config.call_args
        call_kwargs = call_args[1]
        self.assertEqual(call_kwargs["language_code"], "en")
        self.assertEqual(call_kwargs["language_detection"], False)


if __name__ == '__main__':
    unittest.main()
