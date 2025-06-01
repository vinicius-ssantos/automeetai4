from typing import Optional, Dict, Any, List, Union
import os
import openai
from src.interfaces.transcription_service import TranscriptionService
from src.interfaces.config_provider import ConfigProvider
from src.utils.file_utils import validate_file_path
from src.utils.rate_limiter import RateLimiterRegistry
from src.utils.logging import get_logger
from src.models.transcription_result import TranscriptionResult
from src.adapters.whisper_adapter import WhisperAdapter
from src.exceptions import (
    FileError, FileNotFoundError as AutoMeetAIFileNotFoundError,
    APIError, NetworkError, RateLimitError, TranscriptionFailedError
)
from src.config.default_config import (
    OPENAI_API_KEY,
    WHISPER_MODEL,
    WHISPER_LANGUAGE,
    WHISPER_TEMPERATURE,
    WHISPER_RESPONSE_FORMAT,
    OPENAI_RATE_LIMIT,
    OPENAI_RATE_LIMIT_PER,
    OPENAI_RATE_LIMIT_BURST
)

# Check if we're using OpenAI v1.0.0+ or an older version
try:
    from openai import OpenAI
    from openai.types.audio import Transcription
    USING_OPENAI_V1 = True
except ImportError:
    USING_OPENAI_V1 = False


class WhisperTranscriptionService(TranscriptionService):
    """
    Implementação do serviço de transcrição usando OpenAI Whisper.
    Seguindo o Princípio da Responsabilidade Única, esta classe é responsável apenas
    por transcrever arquivos de áudio usando a API Whisper da OpenAI.
    """

    # Inicializa o logger para esta classe
    logger = get_logger(__name__)

    def __init__(self, config_provider: Optional[ConfigProvider] = None):
        """
        Inicializa o serviço de transcrição.

        Args:
            config_provider: Provedor de configuração opcional
        """
        self.config_provider = config_provider

        # Define a chave de API a partir do provedor de configuração ou padrão
        api_key = None
        if self.config_provider:
            api_key = self.config_provider.get("openai_api_key", OPENAI_API_KEY)
        else:
            api_key = OPENAI_API_KEY

        # Valida a chave de API
        self._validate_api_key(api_key)

        # Initialize OpenAI client based on version
        if api_key:
            if USING_OPENAI_V1:
                # For OpenAI v1.0.0+
                self.client = OpenAI(api_key=api_key)
            else:
                # For older versions of OpenAI
                openai.api_key = api_key
                self.client = openai
        else:
            self.client = None

    def _validate_api_key(self, api_key: Optional[str]) -> None:
        """
        Valida a chave de API.

        Args:
            api_key: A chave de API a ser validada

        Raises:
            ValueError: Se a chave de API for inválida
        """
        if not api_key:
            self.logger.warning("OpenAI API key is not provided. Service will be initialized but transcription will not work.")
            return

        if not isinstance(api_key, str):
            raise ValueError("OpenAI API key must be a string.")

        if len(api_key.strip()) < 10:  # Validação básica para o comprimento da chave
            raise ValueError("OpenAI API key appears to be invalid. Please check your API key.")

    def transcribe(self, audio_file: str, config: Optional[Dict[str, Any]] = None,
                 allowed_audio_extensions: Optional[List[str]] = None) -> Union[TranscriptionResult, None]:
        """
        Transcreve um arquivo de áudio para texto usando OpenAI Whisper.

        Args:
            audio_file: Caminho para o arquivo de áudio a ser transcrito
            config: Parâmetros de configuração opcionais para a transcrição
            allowed_audio_extensions: Lista opcional de extensões de arquivo de áudio permitidas

        Returns:
            TranscriptionResult: O resultado da transcrição, ou None se a transcrição falhar
        """
        try:
            # Define extensões permitidas padrão se não fornecidas
            if allowed_audio_extensions is None:
                allowed_audio_extensions = ["mp3", "wav", "ogg", "flac", "m4a"]

            # Valida o caminho do arquivo de áudio
            validate_file_path(audio_file, allowed_extensions=allowed_audio_extensions)

            # Define configuração padrão
            transcription_config = {
                "model": WHISPER_MODEL,
                "language": WHISPER_LANGUAGE,
                "temperature": WHISPER_TEMPERATURE,
                "response_format": WHISPER_RESPONSE_FORMAT
            }

            # Sobrescreve com a configuração fornecida, se houver
            if config:
                transcription_config.update(config)

            # Obtém o limitador de taxa para OpenAI
            rate_limiter = RateLimiterRegistry().get_limiter(
                "openai",
                rate=OPENAI_RATE_LIMIT,
                per=OPENAI_RATE_LIMIT_PER,
                burst=OPENAI_RATE_LIMIT_BURST
            )

            # Aguarda um token ficar disponível (limitação de taxa)
            rate_limiter.consume(wait=True)

            # Verifica se o cliente foi inicializado
            if not self.client:
                error_msg = "OpenAI client is not initialized. Please provide a valid API key."
                self.logger.error(error_msg)
                return None

            # Abre o arquivo de áudio
            with open(audio_file, "rb") as audio:
                # Chama a API Whisper
                self.logger.info(f"Transcrevendo arquivo de áudio: {audio_file}")

                if USING_OPENAI_V1:
                    # For OpenAI v1.0.0+
                    response = self.client.audio.transcriptions.create(
                        file=audio,
                        model=transcription_config["model"],
                        language=transcription_config["language"],
                        temperature=transcription_config["temperature"],
                        response_format=transcription_config["response_format"]
                    )
                else:
                    # For older versions of OpenAI
                    response = self.client.Transcription.create(
                        file=audio,
                        model=transcription_config["model"],
                        language=transcription_config["language"],
                        temperature=transcription_config["temperature"],
                        response_format=transcription_config["response_format"]
                    )

            # Converte para TranscriptionResult
            return WhisperAdapter.convert(response, audio_file)

        except FileNotFoundError:
            error_msg = f"O arquivo de áudio '{audio_file}' não foi encontrado."
            self.logger.error(error_msg)
            return None

        except ValueError as e:
            error_msg = f"Arquivo de áudio ou configuração inválida: {e}"
            self.logger.error(error_msg)
            return None

        except ImportError as e:
            error_msg = f"OpenAI library not properly installed: {e}"
            self.logger.error(error_msg)
            return None

        except ConnectionError as e:
            error_msg = f"Network error during OpenAI API call: {e}"
            self.logger.error(error_msg)
            return None

        except TimeoutError as e:
            error_msg = f"Timeout during OpenAI API call: {e}"
            self.logger.error(error_msg)
            return None

        except Exception as e:
            error_msg = f"Ocorreu um erro durante a transcrição: {e}"
            self.logger.error(error_msg)
            return None
