from typing import Optional, Dict, Any, List, Union, Callable
import time
import threading
import queue
import websocket
import json
import base64
import os
import wave
import math

# Try to import pyaudio, but make it optional
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

from src.interfaces.streaming_transcription_service import StreamingTranscriptionService
from src.interfaces.config_provider import ConfigProvider
from src.utils.logging import get_logger
from src.models.transcription_result import TranscriptionResult
from src.models.streaming_transcription_result import StreamingTranscriptionResult, StreamingSession
from src.config.default_config import (
    ASSEMBLYAI_API_KEY,
    DEFAULT_LANGUAGE_CODE,
    DEFAULT_SPEAKER_LABELS
)


class AssemblyAIStreamingTranscriptionService(StreamingTranscriptionService):
    """
    Implementação do serviço de transcrição em streaming usando AssemblyAI.
    Seguindo o Princípio da Responsabilidade Única, esta classe é responsável apenas
    por transcrever áudio em tempo real usando a API de streaming do AssemblyAI.
    """

    # Inicializa o logger para esta classe
    logger = get_logger(__name__)

    # Configurações do WebSocket do AssemblyAI
    ASSEMBLYAI_STREAMING_URL = "wss://api.assemblyai.com/v2/realtime/ws"

    # Configurações de áudio
    RATE = 16000
    CHANNELS = 1
    CHUNK = 1024
    FORMAT = pyaudio.paInt16 if PYAUDIO_AVAILABLE else 8  # 8 is the value for paInt16

    def __init__(self, config_provider: Optional[ConfigProvider] = None):
        """
        Inicializa o serviço de transcrição em streaming.

        Args:
            config_provider: Provedor de configuração opcional
        """
        self.config_provider = config_provider
        self.session = StreamingSession()
        self.ws = None
        self.audio_queue = queue.Queue()
        self.stop_threads = False
        self.audio_thread = None
        self.processing_thread = None
        self.pyaudio_instance = None
        self.stream = None

        # Define a chave de API a partir do provedor de configuração ou padrão
        self.api_key = None
        if self.config_provider:
            self.api_key = self.config_provider.get("assemblyai_api_key", ASSEMBLYAI_API_KEY)
        else:
            self.api_key = ASSEMBLYAI_API_KEY

        # Valida a chave de API
        self._validate_api_key(self.api_key)

    def _validate_api_key(self, api_key: Optional[str]) -> None:
        """
        Valida a chave de API.

        Args:
            api_key: A chave de API a ser validada

        Raises:
            ValueError: Se a chave de API for inválida
        """
        if not api_key:
            self.logger.warning("AssemblyAI API key is not provided. Service will be initialized but streaming will not work.")
            return

        if not isinstance(api_key, str):
            raise ValueError("AssemblyAI API key must be a string.")

        if len(api_key.strip()) < 10:  # Validação básica para o comprimento da chave
            raise ValueError("AssemblyAI API key appears to be invalid. Please check your API key.")

    def start_streaming(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Inicia uma sessão de transcrição em streaming.

        Args:
            config: Parâmetros de configuração opcionais para a transcrição

        Returns:
            bool: True se a sessão foi iniciada com sucesso, False caso contrário
        """
        # Check if API key is set
        if not self.api_key:
            self.logger.error("Cannot start streaming: AssemblyAI API key is not set. Please set the AUTOMEETAI_ASSEMBLYAI_API_KEY environment variable or provide it directly.")
            return False

        try:
            # Reinicia a sessão
            self.session = StreamingSession()
            self.session.is_active = True
            self.session.start_time = time.time()

            # Define configuração padrão
            self.streaming_config = {
                "language_code": DEFAULT_LANGUAGE_CODE,
                "speaker_labels": DEFAULT_SPEAKER_LABELS,
                "sample_rate": self.RATE
            }

            # Sobrescreve com a configuração fornecida, se houver
            if config:
                self.streaming_config.update(config)

            # Configura o WebSocket
            self.ws = websocket.WebSocketApp(
                self.ASSEMBLYAI_STREAMING_URL,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                header={"Authorization": self.api_key}
            )

            # Inicia o WebSocket em uma thread separada
            self.processing_thread = threading.Thread(target=self.ws.run_forever)
            self.processing_thread.daemon = True
            self.processing_thread.start()

            # Aguarda a conexão ser estabelecida
            time.sleep(1)

            return self.session.is_active

        except Exception as e:
            self.logger.error(f"Erro ao iniciar streaming: {e}")
            self.session.is_active = False
            return False

    def transcribe_chunk(self, audio_chunk: bytes) -> Optional[Dict[str, Any]]:
        """
        Transcreve um fragmento de áudio em tempo real.

        Args:
            audio_chunk: Fragmento de áudio em bytes para transcrever

        Returns:
            Optional[Dict[str, Any]]: Resultado parcial da transcrição, ou None se falhou
        """
        try:
            if not self.is_streaming():
                self.logger.error("Nenhuma sessão de streaming ativa.")
                return None

            # Envia o fragmento de áudio para o WebSocket
            if self.ws and self.ws.sock and self.ws.sock.connected:
                # Codifica o áudio em base64
                audio_base64 = base64.b64encode(audio_chunk).decode("utf-8")

                # Cria o payload
                payload = json.dumps({"audio_data": audio_base64})

                # Envia o payload
                self.ws.send(payload)

                # Retorna o último resultado parcial, se houver
                if self.session.partial_results:
                    return self.session.partial_results[-1].to_dict()

                return {"text": "", "is_final": False}

            return None

        except Exception as e:
            self.logger.error(f"Erro ao transcrever fragmento: {e}")
            return None

    def stop_streaming(self) -> Optional[TranscriptionResult]:
        """
        Finaliza a sessão de transcrição em streaming e retorna o resultado completo.

        Returns:
            Optional[TranscriptionResult]: O resultado completo da transcrição, ou None se falhou
        """
        try:
            if not self.is_streaming():
                self.logger.error("Nenhuma sessão de streaming ativa para finalizar.")
                return None

            # Marca o fim da sessão
            self.session.is_active = False
            self.session.end_time = time.time()

            # Fecha o WebSocket
            if self.ws:
                self.ws.close()

            # Interrompe as threads
            self.stop_threads = True

            # Aguarda as threads terminarem
            if self.audio_thread and self.audio_thread.is_alive():
                self.audio_thread.join(timeout=2)

            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=2)

            # Fecha o stream de áudio, se estiver aberto e se pyaudio está disponível
            if PYAUDIO_AVAILABLE:
                if self.stream:
                    self.stream.stop_stream()
                    self.stream.close()

                if self.pyaudio_instance:
                    self.pyaudio_instance.terminate()

            # Converte a sessão em um TranscriptionResult
            return self.session.to_transcription_result()

        except Exception as e:
            self.logger.error(f"Erro ao finalizar streaming: {e}")
            return None

    def is_streaming(self) -> bool:
        """
        Verifica se uma sessão de streaming está ativa.

        Returns:
            bool: True se uma sessão de streaming está ativa, False caso contrário
        """
        return self.session.is_active

    def stream_microphone(self, 
                        callback: Callable[[Dict[str, Any]], None],
                        duration: Optional[int] = None,
                        config: Optional[Dict[str, Any]] = None) -> Optional[TranscriptionResult]:
        """
        Captura áudio do microfone e transcreve em tempo real.

        Args:
            callback: Função de callback chamada com cada resultado parcial
            duration: Duração máxima da captura em segundos, ou None para continuar até ser interrompido
            config: Parâmetros de configuração opcionais para a transcrição

        Returns:
            Optional[TranscriptionResult]: O resultado completo da transcrição, ou None se falhou
        """
        try:
            # Check if pyaudio is available
            if not PYAUDIO_AVAILABLE:
                self.logger.error("PyAudio is not available. Cannot capture audio from microphone.")
                return None

            # Inicia a sessão de streaming
            if not self.start_streaming(config):
                self.logger.error("Falha ao iniciar a sessão de streaming.")
                return None

            # Inicializa PyAudio
            self.pyaudio_instance = pyaudio.PyAudio()

            # Abre o stream de áudio
            self.stream = self.pyaudio_instance.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )

            # Reinicia a flag de parada
            self.stop_threads = False

            # Função para capturar áudio do microfone
            def audio_capture():
                start_time = time.time()

                while not self.stop_threads:
                    # Verifica se atingiu a duração máxima
                    if duration and time.time() - start_time > duration:
                        break

                    # Lê um fragmento de áudio
                    audio_chunk = self.stream.read(self.CHUNK, exception_on_overflow=False)

                    # Transcreve o fragmento
                    result = self.transcribe_chunk(audio_chunk)

                    # Chama o callback com o resultado
                    if result:
                        callback(result)

                # Finaliza a sessão quando terminar
                self.stop_streaming()

            # Inicia a thread de captura de áudio
            self.audio_thread = threading.Thread(target=audio_capture)
            self.audio_thread.daemon = True
            self.audio_thread.start()

            # Se a duração for especificada, aguarda até o final
            if duration:
                time.sleep(duration)
                return self.stop_streaming()

            # Caso contrário, retorna None e deixa a thread rodando
            return None

        except Exception as e:
            self.logger.error(f"Erro ao capturar áudio do microfone: {e}")
            self.stop_streaming()
            return None

    def _on_open(self, ws):
        """
        Callback chamado quando a conexão WebSocket é aberta.

        Args:
            ws: O objeto WebSocket
        """
        self.logger.info("Conexão WebSocket estabelecida.")

        # Envia a configuração inicial
        config_payload = {
            "sample_rate": self.streaming_config["sample_rate"],
            "language_code": self.streaming_config["language_code"],
            "enable_speaker_diarization": self.streaming_config["speaker_labels"]
        }

        ws.send(json.dumps(config_payload))

    def _on_message(self, ws, message):
        """
        Callback chamado quando uma mensagem é recebida do WebSocket.

        Args:
            ws: O objeto WebSocket
            message: A mensagem recebida
        """
        try:
            # Decodifica a mensagem JSON
            data = json.loads(message)

            # Verifica se é um resultado de transcrição
            if "text" in data:
                # Cria um objeto StreamingTranscriptionResult
                result = StreamingTranscriptionResult(
                    text=data.get("text", ""),
                    is_final=data.get("message_type") == "FinalTranscript",
                    confidence=data.get("confidence", 1.0),
                    speaker=f"Speaker {data.get('speaker')}" if data.get('speaker') else None,
                    start_time=data.get("start", None),
                    end_time=data.get("end", None)
                )

                # Adiciona o resultado à sessão
                self.session.add_result(result)

                self.logger.debug(f"Recebido: {result.text} (final: {result.is_final})")

        except Exception as e:
            self.logger.error(f"Erro ao processar mensagem: {e}")

    def _on_error(self, ws, error):
        """
        Callback chamado quando ocorre um erro no WebSocket.

        Args:
            ws: O objeto WebSocket
            error: O erro ocorrido
        """
        self.logger.error(f"Erro no WebSocket: {error}")
        self.session.is_active = False

    def _on_close(self, ws, close_status_code, close_msg):
        """
        Callback chamado quando a conexão WebSocket é fechada.

        Args:
            ws: O objeto WebSocket
            close_status_code: Código de status de fechamento
            close_msg: Mensagem de fechamento
        """
        self.logger.info(f"Conexão WebSocket fechada: {close_msg} (código: {close_status_code})")
        self.session.is_active = False

    def stream_file(self, 
                  audio_file: str,
                  chunk_size: int = 1024,
                  callback: Optional[Callable[[Dict[str, Any]], None]] = None,
                  progress_callback: Optional[Callable[[float, str], None]] = None,
                  config: Optional[Dict[str, Any]] = None) -> Optional[TranscriptionResult]:
        """
        Processa um arquivo de áudio em streaming para reduzir o uso de memória.

        Este método é especialmente útil para arquivos grandes, pois processa o arquivo
        em pequenos fragmentos em vez de carregá-lo inteiramente na memória.

        Args:
            audio_file: Caminho para o arquivo de áudio a ser transcrito
            chunk_size: Tamanho dos fragmentos de áudio em bytes
            callback: Função de callback chamada com cada resultado parcial
            progress_callback: Função de callback para reportar o progresso (0-100)
            config: Parâmetros de configuração opcionais para a transcrição

        Returns:
            Optional[TranscriptionResult]: O resultado completo da transcrição, ou None se falhou
        """
        try:
            # Verifica se o arquivo existe
            if not os.path.exists(audio_file):
                error_msg = f"O arquivo de áudio '{audio_file}' não foi encontrado."
                self.logger.error(error_msg)
                if progress_callback:
                    progress_callback(0, error_msg)
                return None

            # Reporta progresso inicial
            if progress_callback:
                progress_callback(0, "Iniciando processamento de arquivo em streaming...")

            # Abre o arquivo de áudio
            try:
                with wave.open(audio_file, 'rb') as wf:
                    # Obtém informações do arquivo
                    channels = wf.getnchannels()
                    sample_width = wf.getsampwidth()
                    frame_rate = wf.getframerate()
                    n_frames = wf.getnframes()

                    # Calcula o tamanho total do arquivo em bytes
                    total_size = n_frames * sample_width * channels

                    # Ajusta a configuração com base nas informações do arquivo
                    streaming_config = {
                        "language_code": DEFAULT_LANGUAGE_CODE,
                        "speaker_labels": DEFAULT_SPEAKER_LABELS,
                        "sample_rate": frame_rate
                    }

                    # Sobrescreve com a configuração fornecida, se houver
                    if config:
                        streaming_config.update(config)

                    # Inicia a sessão de streaming
                    if progress_callback:
                        progress_callback(5, "Iniciando sessão de streaming...")

                    if not self.start_streaming(streaming_config):
                        error_msg = "Falha ao iniciar a sessão de streaming."
                        self.logger.error(error_msg)
                        if progress_callback:
                            progress_callback(5, error_msg)
                        return None

                    if progress_callback:
                        progress_callback(10, "Processando arquivo em chunks...")

                    # Processa o arquivo em chunks
                    bytes_processed = 0
                    last_progress = 10

                    # Reinicia a flag de parada
                    self.stop_threads = False

                    while not self.stop_threads:
                        # Lê um chunk do arquivo
                        audio_chunk = wf.readframes(chunk_size)

                        # Se não há mais dados, termina o loop
                        if not audio_chunk:
                            break

                        # Transcreve o chunk
                        result = self.transcribe_chunk(audio_chunk)

                        # Chama o callback com o resultado, se fornecido
                        if callback and result:
                            callback(result)

                        # Atualiza o progresso
                        bytes_processed += len(audio_chunk)
                        progress = min(95, 10 + (bytes_processed / total_size) * 85)

                        # Reporta o progresso apenas se mudou significativamente
                        if progress_callback and progress >= last_progress + 1:
                            progress_callback(progress, f"Processando arquivo... {int(progress)}%")
                            last_progress = progress

                    # Aguarda um pouco para garantir que todos os resultados foram processados
                    time.sleep(1)

                    # Finaliza a sessão de streaming
                    if progress_callback:
                        progress_callback(95, "Finalizando transcrição...")

                    result = self.stop_streaming()

                    if progress_callback:
                        progress_callback(100, "Transcrição concluída com sucesso.")

                    return result

            except wave.Error as e:
                error_msg = f"Erro ao abrir o arquivo de áudio (formato não suportado): {e}"
                self.logger.error(error_msg)
                if progress_callback:
                    progress_callback(0, error_msg)
                return None

        except Exception as e:
            error_msg = f"Erro ao processar arquivo em streaming: {e}"
            self.logger.error(error_msg)
            if progress_callback:
                progress_callback(0, error_msg)

            # Garante que a sessão de streaming seja finalizada
            self.stop_streaming()
            return None
