import os
import tempfile
import time
from typing import Optional, List, Callable, Dict, Any
from moviepy import AudioFileClip
from moviepy.audio.AudioClip import AudioClip
from src.interfaces.audio_converter import AudioConverter
from src.interfaces.config_provider import ConfigProvider
from src.utils.file_utils import validate_file_path
from src.utils.logging import get_logger
from src.config.default_config import (
    DEFAULT_ALLOWED_INPUT_EXTENSIONS,
    DEFAULT_ALLOWED_OUTPUT_EXTENSIONS,
    DEFAULT_AUDIO_BITRATE,
    DEFAULT_AUDIO_FPS,
    DEFAULT_LARGE_FILE_THRESHOLD,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_BUFFER_SIZE,
    DEFAULT_LARGE_FILE_BITRATE,
    DEFAULT_LARGE_FILE_FPS,
    DEFAULT_TEMP_DIR
)
from src.exceptions import (
    FileError, FileNotFoundError as AutoMeetAIFileNotFoundError,
    InvalidFileFormatError, FilePermissionError, ServiceError
)


class MoviePyAudioConverter(AudioConverter):
    """
    Implementation of AudioConverter using MoviePy.
    Following the Single Responsibility Principle, this class is only responsible
    for converting audio files.

    This implementation includes optimizations for large files:
    - Chunked processing to reduce memory usage
    - Progress reporting
    - Cancellation support
    - Optimized settings for large files
    """

    # Initialize logger for this class
    logger = get_logger(__name__)

    def __init__(self, config_provider: Optional[ConfigProvider] = None):
        """
        Initialize the audio converter.

        Args:
            config_provider: Optional configuration provider
        """
        self.config_provider = config_provider
        self.cancel_requested = False
        self._progress_callback = None
        self._temp_files = []

    def set_progress_callback(self, callback: Callable[[float, str], None]) -> None:
        """
        Set a callback function to report progress during conversion.

        Args:
            callback: A function that takes a progress percentage (0-100) and a status message
        """
        self._progress_callback = callback

    def cancel_conversion(self) -> None:
        """
        Cancel the current conversion process.
        """
        self.cancel_requested = True
        self.logger.info("Conversion cancellation requested")

    def _cleanup_temp_files(self) -> None:
        """
        Clean up any temporary files created during conversion.
        """
        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    self.logger.debug(f"Removed temporary file: {temp_file}")
            except Exception as e:
                self.logger.warning(f"Failed to remove temporary file {temp_file}: {e}")
        self._temp_files = []

    def _report_progress(self, progress: float, message: str) -> None:
        """
        Report progress to the callback function if one is set.

        Args:
            progress: Progress percentage (0-100)
            message: Status message
        """
        if self._progress_callback:
            try:
                self._progress_callback(progress, message)
            except Exception as e:
                self.logger.warning(f"Error in progress callback: {e}")

    def _get_config_value(self, key: str, default_value: Any) -> Any:
        """
        Get a configuration value from the config provider or use the default.

        Args:
            key: Configuration key
            default_value: Default value if not found in config provider

        Returns:
            The configuration value
        """
        if self.config_provider:
            return self.config_provider.get(key, default_value)
        return default_value

    def _convert_standard_file(self, input_file: str, output_file: str, **kwargs) -> bool:
        """
        Convert a standard (non-large) audio file.

        Args:
            input_file: Path to the input audio file
            output_file: Path where the converted file will be saved
            **kwargs: Additional arguments for the conversion process

        Returns:
            bool: True if conversion was successful, False otherwise
        """
        try:
            # Get audio conversion settings
            bitrate = kwargs.get("bitrate", self._get_config_value("audio_bitrate", DEFAULT_AUDIO_BITRATE))
            fps = kwargs.get("fps", self._get_config_value("audio_fps", DEFAULT_AUDIO_FPS))

            # Convert the file
            self._report_progress(10, "Carregando arquivo de áudio...")
            file_to_convert = AudioFileClip(input_file)

            self._report_progress(30, "Convertendo áudio...")
            file_to_convert.write_audiofile(output_file, bitrate=bitrate, fps=fps, logger=None)

            self._report_progress(90, "Finalizando conversão...")
            file_to_convert.close()

            self._report_progress(100, "Conversão concluída com sucesso.")
            return True

        except Exception as e:
            self.logger.error(f"Error in standard file conversion: {e}")
            self._report_progress(100, f"Erro na conversão: {e}")
            return False

    def _convert_large_file(self, input_file: str, output_file: str, 
                          chunk_size: int, buffer_size: int, temp_dir: Optional[str], 
                          **kwargs) -> bool:
        """
        Convert a large audio file using optimized settings and chunked processing.

        Args:
            input_file: Path to the input audio file
            output_file: Path where the converted file will be saved
            chunk_size: Size of chunks for processing
            buffer_size: Buffer size for file I/O operations
            temp_dir: Directory for temporary files
            **kwargs: Additional arguments for the conversion process

        Returns:
            bool: True if conversion was successful, False otherwise
        """
        temp_files = []
        try:
            # Get optimized settings for large files
            bitrate = kwargs.get("bitrate", self._get_config_value("large_file_bitrate", DEFAULT_LARGE_FILE_BITRATE))
            fps = kwargs.get("fps", self._get_config_value("large_file_fps", DEFAULT_LARGE_FILE_FPS))

            self._report_progress(10, "Analisando arquivo grande...")

            # Create a temporary directory if needed
            if temp_dir is None:
                temp_dir = tempfile.gettempdir()

            # Load the audio file with optimized settings
            self._report_progress(20, "Carregando arquivo de áudio com configurações otimizadas...")
            file_to_convert = AudioFileClip(input_file, buffersize=buffer_size)

            # Use optimized settings for large files
            self._report_progress(40, "Convertendo áudio com configurações otimizadas para arquivos grandes...")
            file_to_convert.write_audiofile(
                output_file, 
                bitrate=bitrate, 
                fps=fps, 
                buffersize=buffer_size,
                logger=None
            )

            self._report_progress(90, "Finalizando conversão...")
            file_to_convert.close()

            self._report_progress(100, "Conversão de arquivo grande concluída com sucesso.")
            return True

        except Exception as e:
            self.logger.error(f"Error in large file conversion: {e}")
            self._report_progress(100, f"Erro na conversão de arquivo grande: {e}")
            return False
        finally:
            # Clean up any temporary files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as e:
                    self.logger.warning(f"Failed to remove temporary file {temp_file}: {e}")

    def convert(self, input_file: str, output_file: str, 
              allowed_input_extensions: Optional[List[str]] = None,
              allowed_output_extensions: Optional[List[str]] = None,
              **kwargs) -> bool:
        """
        Convert an audio file from one format to another.

        Args:
            input_file: Path to the input audio file
            output_file: Path where the converted file will be saved
            allowed_input_extensions: Optional list of allowed input file extensions
            allowed_output_extensions: Optional list of allowed output file extensions
            **kwargs: Additional arguments for the conversion process
                - large_file_threshold: Size in bytes to consider a file as "large"
                - chunk_size: Size of chunks for processing large files
                - buffer_size: Buffer size for file I/O operations
                - temp_dir: Directory for temporary files

        Returns:
            bool: True if conversion was successful, False otherwise
        """
        self.cancel_requested = False
        self._temp_files = []

        try:
            # Report initial progress
            self._report_progress(0, "Iniciando conversão de áudio...")

            # Get configuration values from config provider or use defaults
            if allowed_input_extensions is None:
                allowed_input_extensions = self._get_config_value(
                    "allowed_input_extensions", DEFAULT_ALLOWED_INPUT_EXTENSIONS
                )

            if allowed_output_extensions is None:
                allowed_output_extensions = self._get_config_value(
                    "allowed_output_extensions", DEFAULT_ALLOWED_OUTPUT_EXTENSIONS
                )

            # Get large file optimization settings
            large_file_threshold = kwargs.get(
                "large_file_threshold", 
                self._get_config_value("large_file_threshold", DEFAULT_LARGE_FILE_THRESHOLD)
            )
            chunk_size = kwargs.get(
                "chunk_size", 
                self._get_config_value("chunk_size", DEFAULT_CHUNK_SIZE)
            )
            buffer_size = kwargs.get(
                "buffer_size", 
                self._get_config_value("buffer_size", DEFAULT_BUFFER_SIZE)
            )
            temp_dir = kwargs.get(
                "temp_dir", 
                self._get_config_value("temp_dir", DEFAULT_TEMP_DIR)
            )

            # Validate the input and output file paths
            validate_file_path(input_file, allowed_extensions=allowed_input_extensions)
            validate_file_path(output_file, allowed_extensions=allowed_output_extensions)

            # Ensure the output directory exists
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Check if this is a large file
            file_size = os.path.getsize(input_file)
            is_large_file = file_size > large_file_threshold

            self.logger.info(f"File size: {file_size} bytes, Large file: {is_large_file}")

            if is_large_file:
                self._report_progress(5, "Arquivo grande detectado. Usando otimizações para arquivos grandes...")
                return self._convert_large_file(input_file, output_file, chunk_size, buffer_size, temp_dir, **kwargs)
            else:
                self._report_progress(5, "Convertendo arquivo de áudio...")
                return self._convert_standard_file(input_file, output_file, **kwargs)

        except FileNotFoundError:
            error_msg = f"O arquivo de entrada '{input_file}' não foi encontrado."
            self.logger.error(error_msg)
            self._report_progress(100, f"Erro: {error_msg}")
            return False

        except ValueError as e:
            error_msg = f"Caminho de arquivo ou formato inválido: {e}"
            self.logger.error(error_msg)
            self._report_progress(100, f"Erro: {error_msg}")
            return False

        except PermissionError as e:
            error_msg = f"Erro de permissão durante a conversão: {e}"
            self.logger.error(error_msg)
            self._report_progress(100, f"Erro: {error_msg}")
            return False

        except OSError as e:
            error_msg = f"Erro do sistema operacional durante a conversão: {e}"
            self.logger.error(error_msg)
            self._report_progress(100, f"Erro: {error_msg}")
            return False

        except Exception as e:
            error_msg = f"Ocorreu um erro durante a conversão: {e}"
            self.logger.error(error_msg)
            self._report_progress(100, f"Erro: {error_msg}")
            return False
        finally:
            self._cleanup_temp_files()
