import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
import shutil

from src.automeetai import AutoMeetAI
from src.models.transcription_result import TranscriptionResult
from src.interfaces.config_provider import ConfigProvider
from src.interfaces.audio_converter import AudioConverter
from src.interfaces.transcription_service import TranscriptionService
from src.interfaces.text_generation_service import TextGenerationService


class TestIntegration(unittest.TestCase):
    """
    Testes de integração para o fluxo de trabalho principal do AutoMeetAI.

    Esta classe de teste verifica se os componentes do AutoMeetAI funcionam
    corretamente juntos em um fluxo de trabalho completo, desde o processamento
    do vídeo até a análise da transcrição.
    """

    def setUp(self):
        """Configuração para cada teste."""
        # Criar diretório temporário para testes
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.output_dir, exist_ok=True)

        # Criar arquivo de vídeo de teste
        self.video_file = os.path.join(self.temp_dir, "test_video.mp4")
        with open(self.video_file, 'w') as f:
            f.write("Mock video content")

        # Criar mocks para os serviços
        self.config_provider = Mock(spec=ConfigProvider)
        self.audio_converter = Mock(spec=AudioConverter)
        self.transcription_service = Mock(spec=TranscriptionService)
        self.text_generation_service = Mock(spec=TextGenerationService)

        # Configurar o ConfigProvider para retornar valores específicos para diferentes chaves
        self.config_provider.get.side_effect = lambda key, default=None: {
            "output_directory": self.output_dir,
            "large_file_threshold": 1000000,  # Return an integer for this key
            "allowed_input_extensions": ["mp4", "avi", "mov", "mkv", "wmv", "flv", "webm"]
        }.get(key, default)

        # Criar a instância do AutoMeetAI com os mocks
        self.app = AutoMeetAI(
            config_provider=self.config_provider,
            audio_converter=self.audio_converter,
            transcription_service=self.transcription_service,
            text_generation_service=self.text_generation_service,
            use_cache=False  # Desabilitar cache para testes
        )

    def tearDown(self):
        """Limpeza após os testes."""
        # Remover diretório temporário
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('src.automeetai.generate_unique_filename')
    @patch('src.automeetai.AssemblyAIAdapter')
    @patch('src.automeetai.validate_file_path')
    @patch('os.path.getsize', return_value=1024)  # Mock file size
    def test_end_to_end_workflow(self, mock_getsize, mock_validate_file_path, mock_adapter, mock_generate_filename):
        """
        Testa o fluxo de trabalho completo do AutoMeetAI.

        Este teste verifica se o processo de conversão de vídeo, transcrição e
        análise funciona corretamente do início ao fim.
        """
        # Configurar o mock para generate_unique_filename
        audio_file = os.path.join(self.output_dir, "test_audio.mp3")
        mock_generate_filename.return_value = audio_file

        # Configurar o mock do AudioConverter
        self.audio_converter.convert.return_value = True

        # Configurar o mock do TranscriptionService
        mock_transcript = Mock()
        mock_transcript.utterances = [{"speaker": "A", "text": "Hello, this is a test."}]
        mock_transcript.text = "Hello, this is a test."
        self.transcription_service.transcribe.return_value = mock_transcript

        # Configurar o mock do AssemblyAIAdapter
        mock_result = Mock(spec=TranscriptionResult)
        mock_result.audio_file = audio_file
        mock_result.utterances = []  # Add empty utterances list to prevent attribute error
        mock_result.to_formatted_text.return_value = "Speaker A: Hello, this is a test."
        mock_result.save_to_file.return_value = True
        mock_adapter.convert.return_value = mock_result

        # Configurar o mock do TextGenerationService
        self.text_generation_service.generate.return_value = "This is an analysis of the meeting."

        # Executar o fluxo de trabalho completo
        # 1. Processar o vídeo
        result = self.app.process_video(
            video_file=self.video_file,
            save_audio=True
        )

        # 2. Analisar a transcrição
        analysis = self.app.analyze_transcription(
            transcription=result,
            system_prompt="Analyze this meeting transcript",
            user_prompt_template="Here is the transcript: {transcription}"
        )

        # Verificar se o resultado da transcrição é o esperado
        self.assertIsNotNone(result)
        self.assertEqual(result, mock_result)

        # Verificar se a análise é a esperada
        self.assertEqual(analysis, "This is an analysis of the meeting.")

        # Verificar se os métodos foram chamados corretamente
        self.audio_converter.convert.assert_called_once_with(self.video_file, audio_file)
        self.transcription_service.transcribe.assert_called_once()
        mock_adapter.convert.assert_called_once_with(mock_transcript, audio_file)
        mock_result.save_to_file.assert_called_once()
        self.text_generation_service.generate.assert_called_once()

    @patch('src.automeetai.generate_unique_filename')
    @patch('src.automeetai.AssemblyAIAdapter')
    @patch('src.automeetai.validate_file_path')
    @patch('os.path.getsize', return_value=1024)  # Mock file size
    def test_workflow_with_multiple_output_formats(self, mock_getsize, mock_validate_file_path, mock_adapter, mock_generate_filename):
        """
        Testa o fluxo de trabalho com múltiplos formatos de saída.

        Este teste verifica se o processo de salvar a transcrição em múltiplos
        formatos funciona corretamente.
        """
        # Configurar o mock para generate_unique_filename
        audio_file = os.path.join(self.output_dir, "test_audio.mp3")
        mock_generate_filename.return_value = audio_file

        # Configurar o mock do AudioConverter
        self.audio_converter.convert.return_value = True

        # Configurar o mock do TranscriptionService
        mock_transcript = Mock()
        mock_transcript.utterances = [{"speaker": "A", "text": "Hello, this is a test."}]
        mock_transcript.text = "Hello, this is a test."
        self.transcription_service.transcribe.return_value = mock_transcript

        # Configurar o mock do AssemblyAIAdapter
        mock_result = Mock(spec=TranscriptionResult)
        mock_result.audio_file = audio_file
        mock_result.utterances = []  # Add empty utterances list to prevent attribute error
        mock_result.save_as_multiple_formats.return_value = {"txt": True, "json": True}
        mock_adapter.convert.return_value = mock_result

        # Executar o processamento de vídeo com múltiplos formatos
        result = self.app.process_video(
            video_file=self.video_file,
            output_formats=["txt", "json"]
        )

        # Verificar se o resultado da transcrição é o esperado
        self.assertIsNotNone(result)

        # Verificar se os métodos foram chamados corretamente
        mock_result.save_as_multiple_formats.assert_called_once_with(
            os.path.splitext(audio_file)[0],
            ["txt", "json"],
            None
        )

    @patch('src.automeetai.generate_unique_filename')
    @patch('src.automeetai.validate_file_path')
    @patch('os.path.getsize', return_value=1024)  # Mock file size
    def test_workflow_with_audio_conversion_failure(self, mock_getsize, mock_validate_file_path, mock_generate_filename):
        """
        Testa o fluxo de trabalho quando a conversão de áudio falha.

        Este teste verifica se o processo lida corretamente com falhas na
        conversão de áudio.
        """
        # Configurar o mock para generate_unique_filename
        audio_file = os.path.join(self.output_dir, "test_audio.mp3")
        mock_generate_filename.return_value = audio_file

        # Configurar o mock do AudioConverter para falhar
        self.audio_converter.convert.return_value = False

        # Executar o processamento de vídeo
        with self.assertRaises(Exception) as context:
            self.app.process_video(
                video_file=self.video_file
            )

        # Verificar se a exceção correta foi lançada
        self.assertIn("Audio conversion failed", str(context.exception))

        # Verificar se os métodos foram chamados corretamente
        self.audio_converter.convert.assert_called_once()
        self.transcription_service.transcribe.assert_not_called()

    @patch('src.automeetai.generate_unique_filename')
    @patch('src.automeetai.AssemblyAIAdapter')
    @patch('src.automeetai.validate_file_path')
    @patch('os.path.getsize', return_value=1024)  # Mock file size
    def test_workflow_with_transcription_failure(self, mock_getsize, mock_validate_file_path, mock_adapter, mock_generate_filename):
        """
        Testa o fluxo de trabalho quando a transcrição falha.

        Este teste verifica se o processo lida corretamente com falhas na
        transcrição.
        """
        # Configurar o mock para generate_unique_filename
        audio_file = os.path.join(self.output_dir, "test_audio.mp3")
        mock_generate_filename.return_value = audio_file

        # Configurar o mock do AudioConverter
        self.audio_converter.convert.return_value = True

        # Configurar o mock do TranscriptionService para falhar
        self.transcription_service.transcribe.return_value = None

        # Executar o processamento de vídeo
        with self.assertRaises(Exception) as context:
            self.app.process_video(
                video_file=self.video_file
            )

        # Verificar se a exceção correta foi lançada
        self.assertIn("Transcription service returned empty result", str(context.exception))

        # Verificar se os métodos foram chamados corretamente
        self.audio_converter.convert.assert_called_once()
        self.transcription_service.transcribe.assert_called_once()
        mock_adapter.convert.assert_not_called()


if __name__ == '__main__':
    unittest.main()
