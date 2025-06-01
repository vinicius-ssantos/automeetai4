import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile

from src.services.moviepy_audio_converter import MoviePyAudioConverter
from src.interfaces.config_provider import ConfigProvider


class TestMoviePyAudioConverter(unittest.TestCase):
    """
    Testes para o MoviePyAudioConverter.

    Esta classe de teste verifica se o MoviePyAudioConverter converte
    corretamente arquivos de áudio usando a biblioteca MoviePy.
    """

    def setUp(self):
        """Configuração para cada teste."""
        # Criar um mock para o ConfigProvider
        self.config_provider = Mock(spec=ConfigProvider)

        # Configurar valores padrão para o mock
        self.config_provider.get.side_effect = lambda key, default=None: {
            "allowed_input_extensions": ["mp4", "avi", "mov"],
            "allowed_output_extensions": ["mp3", "wav"],
            "large_file_threshold": 10000000,  # 10MB
            "audio_bitrate": "192k",
            "audio_fps": 44100
        }.get(key, default)

        # Criar o conversor com o mock do ConfigProvider
        self.converter = MoviePyAudioConverter(self.config_provider)

        # Criar diretório temporário para testes
        self.temp_dir = tempfile.mkdtemp()

        # Caminhos de arquivos para testes
        self.input_file = os.path.join(self.temp_dir, "test_input.mp4")
        self.output_file = os.path.join(self.temp_dir, "test_output.mp3")

    def tearDown(self):
        """Limpeza após os testes."""
        # Remover diretório temporário
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('src.services.moviepy_audio_converter.validate_file_path')
    @patch('src.services.moviepy_audio_converter.AudioFileClip')
    @patch('src.services.moviepy_audio_converter.os.path.getsize')
    def test_convert_success(self, mock_getsize, mock_audio_clip, mock_validate):
        """Testa a conversão bem-sucedida de um arquivo."""
        # Configurar mocks
        mock_getsize.return_value = 1024  # Simular um arquivo pequeno
        mock_clip_instance = mock_audio_clip.return_value

        # Chamar o método convert
        result = self.converter.convert(
            input_file=self.input_file,
            output_file=self.output_file
        )

        # Verificar se o resultado é True (sucesso)
        self.assertTrue(result)

        # Verificar se os métodos foram chamados corretamente
        mock_validate.assert_called()
        mock_audio_clip.assert_called_once_with(self.input_file)
        mock_clip_instance.write_audiofile.assert_called_once()
        mock_clip_instance.close.assert_called_once()

    @patch('src.services.moviepy_audio_converter.validate_file_path')
    @patch('src.services.moviepy_audio_converter.AudioFileClip')
    @patch('src.services.moviepy_audio_converter.os.path.getsize')
    def test_convert_with_custom_config(self, mock_getsize, mock_audio_clip, mock_validate):
        """Testa a conversão com configurações personalizadas."""
        # Configurar mocks para retornar valores específicos
        mock_getsize.return_value = 1024  # Simular um arquivo pequeno
        self.config_provider.get.side_effect = lambda key, default: {
            "allowed_input_extensions": ["mp4", "avi"],
            "allowed_output_extensions": ["mp3", "wav"],
            "audio_bitrate": "192k",
            "audio_fps": 44100
        }.get(key, default)

        mock_clip_instance = mock_audio_clip.return_value

        # Chamar o método convert
        result = self.converter.convert(
            input_file=self.input_file,
            output_file=self.output_file
        )

        # Verificar se o resultado é True (sucesso)
        self.assertTrue(result)

        # Verificar se os métodos foram chamados corretamente
        mock_audio_clip.assert_called_once_with(self.input_file)
        mock_clip_instance.write_audiofile.assert_called_once()

        # Verificar se o ConfigProvider foi consultado para as configurações
        self.config_provider.get.assert_any_call("audio_bitrate", unittest.mock.ANY)
        self.config_provider.get.assert_any_call("audio_fps", unittest.mock.ANY)

    @patch('src.services.moviepy_audio_converter.validate_file_path')
    def test_convert_file_not_found(self, mock_validate):
        """Testa o comportamento quando o arquivo de entrada não é encontrado."""
        # Configurar mock para lançar FileNotFoundError
        mock_validate.side_effect = FileNotFoundError("File not found")

        # Chamar o método convert
        result = self.converter.convert(
            input_file=self.input_file,
            output_file=self.output_file
        )

        # Verificar se o resultado é False (falha)
        self.assertFalse(result)

    @patch('src.services.moviepy_audio_converter.validate_file_path')
    @patch('src.services.moviepy_audio_converter.AudioFileClip')
    @patch('src.services.moviepy_audio_converter.os.path.getsize')
    def test_convert_permission_error(self, mock_getsize, mock_audio_clip, mock_validate):
        """Testa o comportamento quando ocorre um erro de permissão."""
        # Configurar mock para lançar PermissionError
        mock_getsize.return_value = 1024  # Simular um arquivo pequeno
        mock_clip_instance = mock_audio_clip.return_value
        mock_clip_instance.write_audiofile.side_effect = PermissionError("Permission denied")

        # Chamar o método convert
        result = self.converter.convert(
            input_file=self.input_file,
            output_file=self.output_file
        )

        # Verificar se o resultado é False (falha)
        self.assertFalse(result)

    @patch('src.services.moviepy_audio_converter.validate_file_path')
    @patch('src.services.moviepy_audio_converter.AudioFileClip')
    @patch('src.services.moviepy_audio_converter.os.path.getsize')
    def test_convert_general_exception(self, mock_getsize, mock_audio_clip, mock_validate):
        """Testa o comportamento quando ocorre uma exceção genérica."""
        # Configurar mock para lançar Exception
        mock_getsize.return_value = 1024  # Simular um arquivo pequeno
        mock_clip_instance = mock_audio_clip.return_value
        mock_clip_instance.write_audiofile.side_effect = Exception("General error")

        # Chamar o método convert
        result = self.converter.convert(
            input_file=self.input_file,
            output_file=self.output_file
        )

        # Verificar se o resultado é False (falha)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
