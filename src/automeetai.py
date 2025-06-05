import os
import concurrent.futures
from typing import Optional, Dict, Any, List, Callable, Union, Tuple

from src.interfaces.audio_converter import AudioConverter
from src.interfaces.transcription_service import TranscriptionService
from src.interfaces.streaming_transcription_service import StreamingTranscriptionService
from src.interfaces.text_generation_service import TextGenerationService
from src.interfaces.config_provider import ConfigProvider
from src.models.transcription_result import TranscriptionResult
from src.models.optimized_transcription_result import OptimizedTranscriptionResult
from src.adapters.assemblyai_adapter import AssemblyAIAdapter
from src.utils.file_utils import generate_unique_filename, ensure_directory_exists, validate_file_path
from src.utils.logging import get_logger
from src.utils.transcription_cache import TranscriptionCache
from src.utils.lazy_text_processor import LazyTextProcessor
from src.utils.error_messages import get_user_friendly_message
from src.utils.cancellation_manager import CancellationManager
from src.interfaces.message_queue import MessageQueue
from src.config.default_config import (
    DEFAULT_OUTPUT_DIRECTORY,
    DEFAULT_MAX_WORKERS,
    DEFAULT_PARALLEL_PROCESSING,
    DEFAULT_CHUNK_SIZE_PARALLEL,
    DEFAULT_LARGE_FILE_THRESHOLD,
    DEFAULT_USE_STREAMING_FOR_LARGE_FILES,
    DEFAULT_STREAMING_CHUNK_SIZE,
    DEFAULT_USE_OPTIMIZED_TRANSCRIPTION_RESULT,
    DEFAULT_LARGE_TRANSCRIPTION_THRESHOLD,
    DEFAULT_UTTERANCE_CHUNK_SIZE,
    DEFAULT_USE_LAZY_TEXT_PROCESSING,
    DEFAULT_TEXT_PROCESSING_CHUNK_SIZE,
    DEFAULT_TEXT_PROCESSING_MAX_CHUNKS
)
from src.exceptions import (
    AutoMeetAIError, FileError, ServiceError, TranscriptionError, 
    FormattingError, UnsupportedFormatError, FormattingFailedError
)


class AutoMeetAI:
    """
    Classe principal da aplicação que orquestra o fluxo de trabalho.

    Seguindo o Princípio da Responsabilidade Única (SRP), esta classe é responsável por
    coordenar o fluxo de trabalho entre os diferentes serviços, delegando tarefas específicas
    para os componentes especializados.

    Esta classe atua como um ponto central de coordenação, utilizando os serviços injetados
    para realizar a conversão de áudio, transcrição e análise de texto.

    A classe também fornece suporte para cancelamento de operações em andamento, permitindo
    que o usuário cancele operações de longa duração a qualquer momento.
    """

    # Initialize logger for this class
    logger = get_logger(__name__)

    def __init__(
        self,
        config_provider: ConfigProvider,
        audio_converter: AudioConverter,
        transcription_service: TranscriptionService,
        text_generation_service: TextGenerationService,
        use_cache: bool = True,
        cache_dir: str = "cache"
    ):
        """
        Inicializa a aplicação AutoMeetAI.

        Este método configura a instância da aplicação com os serviços necessários
        para seu funcionamento. Seguindo o princípio de Injeção de Dependência,
        todos os serviços principais são fornecidos externamente, permitindo maior
        flexibilidade e testabilidade.

        Args:
            config_provider: Provedor de configuração que fornece acesso às configurações da aplicação
            audio_converter: Serviço de conversão de áudio para transformar vídeos em arquivos de áudio
            transcription_service: Serviço de transcrição para converter áudio em texto
            text_generation_service: Serviço de geração de texto para análise das transcrições (pode ser uma implementação real ou nula)
            use_cache: Indica se o cache de transcrições deve ser utilizado para evitar reprocessamento
            cache_dir: Diretório onde os arquivos de cache serão armazenados
        """
        self.config_provider = config_provider
        self.audio_converter = audio_converter
        self.transcription_service = transcription_service
        self.text_generation_service = text_generation_service
        self.use_cache = use_cache

        # Get output directory from config
        self.output_directory = self.config_provider.get(
            "output_directory", 
            DEFAULT_OUTPUT_DIRECTORY
        )

        # Ensure output directory exists
        ensure_directory_exists(self.output_directory)

        # Initialize transcription cache if enabled
        self.transcription_cache = None
        if self.use_cache:
            self.transcription_cache = TranscriptionCache(cache_dir)

        # Initialize cancellation manager
        self.cancellation_manager = CancellationManager()

        # Fila de mensagens opcional para processamento assíncrono
        self.message_queue: Optional[MessageQueue] = None

    def request_cancellation(self, reason: Optional[str] = None) -> None:
        """
        Solicita o cancelamento da operação atual.

        Este método permite que o usuário cancele uma operação em andamento,
        como processamento de vídeo, transcrição ou análise de texto.

        Args:
            reason: Motivo opcional para o cancelamento
        """
        self.cancellation_manager.request_cancellation(reason)
        self.logger.info(f"Cancelamento solicitado: {reason if reason else 'Sem motivo especificado'}")

    def is_cancellation_requested(self) -> bool:
        """
        Verifica se o cancelamento foi solicitado.

        Returns:
            bool: True se o cancelamento foi solicitado, False caso contrário
        """
        return self.cancellation_manager.is_cancellation_requested()

    def reset_cancellation(self) -> None:
        """
        Reinicia o estado de cancelamento.

        Este método deve ser chamado antes de iniciar uma nova operação
        para garantir que o estado de cancelamento esteja limpo.
        """
        self.cancellation_manager.reset()
        self.logger.info("Estado de cancelamento reiniciado")

    def set_message_queue(self, queue: MessageQueue) -> None:
        """Define a fila de mensagens da aplicação.

        Args:
            queue: Instância da fila a ser utilizada.
        """
        self.message_queue = queue

    def iniciar_fila(self, num_workers: int = 1) -> None:
        """Inicia a fila de mensagens, se configurada."""
        if self.message_queue:
            self.message_queue.iniciar(num_workers)

    def parar_fila(self) -> None:
        """Encerra a fila de mensagens, se configurada."""
        if self.message_queue:
            self.message_queue.parar()

    def enfileirar_video(self, video_file: str) -> None:
        """Publica um arquivo de vídeo para processamento assíncrono."""
        if not self.message_queue:
            raise AutoMeetAIError("Fila de mensagens não configurada")
        self.message_queue.publicar(video_file)

    def _get_allowed_video_extensions(
        self, allowed_video_extensions: Optional[List[str]]
    ) -> List[str]:
        """Retorna a lista de extensões de vídeo permitidas.

        Args:
            allowed_video_extensions: Lista fornecida pelo usuário.

        Returns:
            List[str]: Lista final de extensões permitidas.
        """
        if allowed_video_extensions is not None:
            return allowed_video_extensions
        return self.config_provider.get(
            "allowed_input_extensions",
            ["mp4", "avi", "mov", "mkv", "wmv", "flv", "webm"],
        )

    def _validate_video_file(
        self, video_file: str, allowed_video_extensions: Optional[List[str]]
    ) -> None:
        """Valida o caminho do arquivo de vídeo informado.

        Args:
            video_file: Caminho do arquivo de vídeo.
            allowed_video_extensions: Extensões de vídeo permitidas.

        Raises:
            ValueError: Se o arquivo for inválido.
        """
        validate_file_path(
            video_file, allowed_extensions=self._get_allowed_video_extensions(allowed_video_extensions)
        )

    def _generate_audio_filename(self) -> str:
        """Gera um nome de arquivo único para o áudio de saída."""
        return generate_unique_filename("mp3", directory=self.output_directory)

    def process_video(
        self, 
        video_file: str, 
        transcription_config: Optional[Dict[str, Any]] = None,
        save_audio: bool = False,
        allowed_video_extensions: Optional[List[str]] = None,
        force_reprocess: bool = False,
        output_format: str = "txt",
        output_formats: Optional[List[str]] = None,
        format_options: Optional[Dict[str, Dict[str, Any]]] = None,
        progress_callback: Optional[Callable[[str, Union[int, float], Union[int, float]], None]] = None,
        cancellation_check: Optional[Callable[[], bool]] = None,
        use_internal_cancellation: bool = True
    ) -> Optional[TranscriptionResult]:
        """
        Processa um arquivo de vídeo: converte para áudio e transcreve.

        Este método executa o fluxo principal da aplicação, coordenando as seguintes etapas:
        1. Validação do arquivo de vídeo
        2. Verificação de cache (se habilitado)
        3. Conversão do vídeo para áudio
        4. Transcrição do áudio
        5. Formatação e salvamento dos resultados
        6. Armazenamento em cache (se habilitado)

        O método implementa tratamento de erros robusto, capturando e convertendo exceções
        em tipos específicos para facilitar o tratamento pelo código cliente.

        O método também suporta cancelamento de operações em andamento, permitindo que o usuário
        cancele o processamento a qualquer momento.

        Args:
            video_file: Caminho para o arquivo de vídeo a ser processado
            transcription_config: Configuração opcional para o serviço de transcrição
            save_audio: Indica se o arquivo de áudio intermediário deve ser preservado
            allowed_video_extensions: Lista opcional de extensões de vídeo permitidas
            force_reprocess: Força o reprocessamento mesmo se existir um resultado em cache
            output_format: Formato para salvar o resultado da transcrição (padrão: "txt")
            output_formats: Lista de formatos para salvar o resultado (se fornecido, substitui output_format)
            format_options: Dicionário mapeando formatos para suas opções específicas
            progress_callback: Função de callback para reportar o progresso da operação.
                              Recebe três parâmetros: (1) descrição da etapa atual, (2) valor atual do progresso,
                              (3) valor total/máximo do progresso
            cancellation_check: Função opcional que retorna True se a operação deve ser cancelada.
                              Esta função é chamada em pontos-chave durante o processamento para verificar
                              se o usuário solicitou o cancelamento da operação.
            use_internal_cancellation: Indica se o gerenciador de cancelamento interno deve ser usado.
                                     Se True, o método também verificará o estado de cancelamento interno,
                                     permitindo que o cancelamento seja solicitado através do método
                                     request_cancellation().

        Returns:
            Optional[TranscriptionResult]: O resultado da transcrição, ou None se o processamento falhar

        Raises:
            FileError: Se houver um problema com o arquivo de vídeo ou arquivos de saída
            ServiceError: Se houver um problema com serviços externos
            TranscriptionError: Se houver um problema com o processo de transcrição
            FormattingError: Se houver um problema com a formatação da saída
            AutoMeetAIError: Para quaisquer outros erros específicos da aplicação
        """
        try:
            # Reset the cancellation state if using internal cancellation
            if use_internal_cancellation:
                self.reset_cancellation()
                # Store metadata about the operation
                self.cancellation_manager.set_metadata("operation_type", "process_video")
                self.cancellation_manager.set_metadata("file_path", video_file)

            # Define the total number of steps for progress reporting
            total_steps = 5  # Validation, Cache Check, Conversion, Transcription, Saving
            current_step = 0

            # Helper function to report progress
            def report_progress(stage: str, step_progress: float = 1.0):
                nonlocal current_step
                if progress_callback:
                    progress_callback(stage, current_step + step_progress, total_steps)

            # Helper function to check for cancellation
            def check_cancellation():
                # Check external cancellation function if provided
                if cancellation_check and cancellation_check():
                    self.logger.info(f"Operation cancelled by user (external): {video_file}")
                    raise AutoMeetAIError("Operação cancelada pelo usuário")

                # Check internal cancellation state if enabled
                if use_internal_cancellation and self.is_cancellation_requested():
                    reason = self.cancellation_manager.get_cancellation_reason()
                    self.logger.info(f"Operation cancelled by user (internal): {video_file}, reason: {reason}")
                    raise AutoMeetAIError(f"Operação cancelada pelo usuário: {reason}" if reason else "Operação cancelada pelo usuário")

            # Step 1: Validation
            current_step = 0
            report_progress("Validando arquivo de entrada", 0.5)

            try:
                self._validate_video_file(video_file, allowed_video_extensions)
                report_progress("Arquivo validado", 1.0)
                # Check for cancellation after validation
                check_cancellation()
            except ValueError as e:
                raise FileError(f"Invalid video file: {e}") from e

            # Step 2: Check cache
            current_step = 1
            report_progress("Verificando cache", 0.5)

            # Check cache if enabled and not forcing reprocess
            if self.use_cache and self.transcription_cache and not force_reprocess:
                try:
                    cached_result = self.transcription_cache.get(video_file)
                    if cached_result:
                        self.logger.info(f"Using cached transcription for {video_file}")
                        report_progress("Usando resultado em cache", 1.0)
                        # Report completion of all steps since we're using cached result
                        report_progress("Processamento concluído", total_steps)
                        return cached_result
                except Exception as e:
                    self.logger.warning(f"Failed to retrieve from cache: {e}")
                    # Continue with normal processing if cache retrieval fails

            report_progress("Cache verificado", 1.0)
            # Check for cancellation after cache check
            check_cancellation()

            # Generate a unique filename for the audio file
            try:
                audio_file = self._generate_audio_filename()
            except Exception as e:
                raise FileError(f"Failed to generate output filename: {e}") from e

            # Step 3: Convert video to audio
            current_step = 2
            report_progress("Iniciando conversão de vídeo para áudio", 0.1)
            self.logger.info(f"Converting {video_file} to audio...")

            try:
                # Report progress before starting conversion
                report_progress("Convertendo vídeo para áudio", 0.5)

                conversion_success = self.audio_converter.convert(video_file, audio_file)
                if not conversion_success:
                    raise ServiceError("Audio conversion failed")

                report_progress("Conversão concluída", 1.0)
                # Check for cancellation after conversion
                check_cancellation()
            except Exception as e:
                if isinstance(e, ServiceError):
                    raise
                raise ServiceError(f"Error during audio conversion: {e}") from e

            # Step 4: Transcribe the audio
            current_step = 3
            report_progress("Iniciando transcrição", 0.1)
            self.logger.info(f"Transcribing {audio_file}...")

            try:
                # Report progress before starting transcription
                report_progress("Transcrevendo áudio", 0.5)

                # Check if the file is large and if we should use streaming
                use_streaming = self.config_provider.get(
                    "use_streaming_for_large_files", 
                    DEFAULT_USE_STREAMING_FOR_LARGE_FILES
                )

                large_file_threshold = self.config_provider.get(
                    "large_file_threshold", 
                    DEFAULT_LARGE_FILE_THRESHOLD
                )

                streaming_chunk_size = self.config_provider.get(
                    "streaming_chunk_size", 
                    DEFAULT_STREAMING_CHUNK_SIZE
                )

                # Check if the file is large
                file_size = os.path.getsize(audio_file)
                is_large_file = file_size > large_file_threshold

                # Check if the transcription service supports streaming
                supports_streaming = isinstance(self.transcription_service, StreamingTranscriptionService)

                # Log the decision
                self.logger.info(f"File size: {file_size} bytes, Large file: {is_large_file}, Use streaming: {use_streaming}, Supports streaming: {supports_streaming}")

                # Use streaming for large files if supported and enabled
                if is_large_file and use_streaming and supports_streaming:
                    self.logger.info(f"Using streaming transcription for large file: {audio_file}")

                    # Create a progress callback wrapper for streaming
                    def streaming_progress_callback(progress: float, message: str) -> None:
                        # Map the streaming progress (0-100) to the transcription step progress (0.5-1.0)
                        step_progress = 0.5 + (progress / 100) * 0.5
                        report_progress(message, step_progress)
                        # Check for cancellation periodically during streaming
                        if progress % 10 < 1:  # Check approximately every 10% progress
                            check_cancellation()

                    # Use the streaming transcription service
                    streaming_service = self.transcription_service
                    transcript = streaming_service.stream_file(
                        audio_file=audio_file,
                        chunk_size=streaming_chunk_size,
                        config=transcription_config,
                        progress_callback=streaming_progress_callback
                    )
                else:
                    # Use the regular transcription service
                    transcript = self.transcription_service.transcribe(audio_file, transcription_config)

                if not transcript:
                    raise TranscriptionError("Transcription service returned empty result")

                report_progress("Transcrição concluída", 1.0)
                # Check for cancellation after transcription
                check_cancellation()
            except Exception as e:
                if isinstance(e, TranscriptionError):
                    raise
                raise TranscriptionError(f"Error during transcription: {e}") from e

            # Create a TranscriptionResult object using the adapter
            try:
                # Get the standard transcription result
                standard_result = AssemblyAIAdapter.convert(transcript, audio_file)

                # Check if we should use the optimized model
                use_optimized = self.config_provider.get(
                    "use_optimized_transcription_result", 
                    DEFAULT_USE_OPTIMIZED_TRANSCRIPTION_RESULT
                )

                large_transcription_threshold = self.config_provider.get(
                    "large_transcription_threshold", 
                    DEFAULT_LARGE_TRANSCRIPTION_THRESHOLD
                )

                utterance_chunk_size = self.config_provider.get(
                    "utterance_chunk_size", 
                    DEFAULT_UTTERANCE_CHUNK_SIZE
                )

                # Check if this is a large transcription
                is_large_transcription = len(standard_result.utterances) > large_transcription_threshold

                # Log the decision
                self.logger.info(f"Utterance count: {len(standard_result.utterances)}, Large transcription: {is_large_transcription}, Use optimized: {use_optimized}")

                # Use optimized model for large transcriptions if enabled
                if is_large_transcription and use_optimized:
                    self.logger.info(f"Using optimized transcription result model for large transcription")
                    result = OptimizedTranscriptionResult.from_standard_result(standard_result)
                else:
                    result = standard_result

            except Exception as e:
                raise TranscriptionError(f"Failed to convert transcription result: {e}") from e

            # Step 5: Save the transcription to a file or files
            current_step = 4
            report_progress("Iniciando salvamento dos resultados", 0.1)
            base_output_file = os.path.splitext(audio_file)[0]

            # If multiple output formats are specified, save in all formats
            if output_formats:
                try:
                    report_progress("Salvando em múltiplos formatos", 0.5)

                    format_results = result.save_as_multiple_formats(
                        base_output_file, 
                        output_formats, 
                        format_options
                    )

                    for format_name, success in format_results.items():
                        if success:
                            self.logger.info(f"Transcription saved in {format_name} format")
                        else:
                            self.logger.error(f"Failed to save transcription in {format_name} format")

                    report_progress("Salvamento concluído", 1.0)
                    # Check for cancellation after saving in multiple formats
                    check_cancellation()
                except Exception as e:
                    if isinstance(e, (UnsupportedFormatError, FormattingFailedError, FileError)):
                        raise
                    raise FormattingError(f"Error saving in multiple formats: {e}") from e

            # Otherwise, save in the single specified format
            else:
                output_file = f"{base_output_file}.{output_format}"
                format_specific_options = None
                if format_options and output_format in format_options:
                    format_specific_options = format_options[output_format]

                try:
                    report_progress(f"Salvando no formato {output_format}", 0.5)

                    success = result.save_to_file(output_file, output_format, format_specific_options)
                    if success:
                        self.logger.info(f"Transcription saved to {output_file}")
                        report_progress("Salvamento concluído", 1.0)
                        # Check for cancellation after saving in single format
                        check_cancellation()
                    else:
                        raise FormattingError(f"Failed to save transcription to {output_file}")
                except Exception as e:
                    if isinstance(e, (UnsupportedFormatError, FormattingFailedError, FileError)):
                        raise
                    raise FormattingError(f"Error saving to {output_format} format: {e}") from e

            # Store the result in cache if enabled
            if self.use_cache and self.transcription_cache:
                try:
                    # Check for cancellation before caching
                    check_cancellation()
                    self.transcription_cache.set(video_file, result)
                except Exception as e:
                    self.logger.warning(f"Failed to store in cache: {e}")
                    # Continue even if caching fails

            # Delete the audio file if not saving
            if not save_audio and os.path.exists(audio_file):
                try:
                    # Check for cancellation before deleting audio file
                    check_cancellation()
                    os.remove(audio_file)
                except Exception as e:
                    self.logger.warning(f"Failed to delete temporary audio file: {e}")
                    # Continue even if file deletion fails

            # Final progress report
            report_progress("Processamento concluído", 1.0)

            return result

        except AutoMeetAIError as e:
            # Log and re-raise application-specific exceptions with user-friendly message
            self.logger.error(f"{e.__class__.__name__}: {e}")
            # Add user-friendly message to the exception
            e.user_friendly_message = get_user_friendly_message(e, {'file_path': video_file})
            raise
        except Exception as e:
            # Convert and log unexpected exceptions
            self.logger.error(f"Unexpected error processing video: {e}")
            error = AutoMeetAIError(f"Unexpected error processing video: {e}")
            error.user_friendly_message = get_user_friendly_message(e, {'file_path': video_file})
            raise error from e

    def process_videos(
        self,
        video_files: List[str],
        transcription_config: Optional[Dict[str, Any]] = None,
        save_audio: bool = False,
        allowed_video_extensions: Optional[List[str]] = None,
        force_reprocess: bool = False,
        output_format: str = "txt",
        output_formats: Optional[List[str]] = None,
        format_options: Optional[Dict[str, Dict[str, Any]]] = None,
        continue_on_error: bool = True,
        progress_callback: Optional[Callable[[str, Union[int, float], Union[int, float]], None]] = None,
        parallel_processing: Optional[bool] = None,
        max_workers: Optional[int] = None,
        chunk_size: Optional[int] = None,
        cancellation_check: Optional[Callable[[], bool]] = None,
        use_internal_cancellation: bool = True
    ) -> Dict[str, Optional[TranscriptionResult]]:
        """
        Processa múltiplos arquivos de vídeo em lote, com suporte a processamento paralelo.

        Este método permite o processamento em lote de vários arquivos de vídeo,
        aplicando as mesmas configurações para todos os arquivos. O método:
        1. Itera sobre cada arquivo de vídeo na lista (sequencialmente ou em paralelo)
        2. Processa cada arquivo usando o método process_video
        3. Coleta os resultados e erros para cada arquivo
        4. Retorna um dicionário mapeando cada arquivo ao seu resultado

        Quando o processamento paralelo está ativado, os arquivos são processados
        simultaneamente usando múltiplas threads, o que pode melhorar significativamente
        o desempenho, especialmente para grandes lotes de arquivos.

        Args:
            video_files: Lista de caminhos para os arquivos de vídeo a serem processados
            transcription_config: Configuração opcional para o serviço de transcrição
            save_audio: Indica se os arquivos de áudio intermediários devem ser preservados
            allowed_video_extensions: Lista opcional de extensões de vídeo permitidas
            force_reprocess: Força o reprocessamento mesmo se existir um resultado em cache
            output_format: Formato para salvar o resultado da transcrição (padrão: "txt")
            output_formats: Lista de formatos para salvar o resultado (se fornecido, substitui output_format)
            format_options: Dicionário mapeando formatos para suas opções específicas
            continue_on_error: Se True, continua processando os arquivos restantes mesmo se ocorrer um erro
            progress_callback: Função de callback para reportar o progresso da operação.
                              Recebe três parâmetros: (1) descrição da etapa atual, (2) valor atual do progresso,
                              (3) valor total/máximo do progresso
            parallel_processing: Se True, processa os arquivos em paralelo. Se None, usa o valor padrão da configuração.
            max_workers: Número máximo de workers para processamento paralelo. Se None, usa o valor padrão da configuração.
            chunk_size: Número de arquivos a serem processados por cada worker. Se None, usa o valor padrão da configuração.
            cancellation_check: Função opcional que retorna True se a operação deve ser cancelada.
                              Esta função é chamada em pontos-chave durante o processamento para verificar
                              se o usuário solicitou o cancelamento da operação.
            use_internal_cancellation: Indica se o gerenciador de cancelamento interno deve ser usado.
                                     Se True, o método também verificará o estado de cancelamento interno,
                                     permitindo que o cancelamento seja solicitado através do método
                                     request_cancellation().

        Returns:
            Dict[str, Optional[TranscriptionResult]]: Dicionário mapeando cada arquivo ao seu resultado de transcrição,
            ou None se o processamento daquele arquivo falhar

        Raises:
            AutoMeetAIError: Se ocorrer um erro durante o processamento e continue_on_error for False
        """
        # Reset the cancellation state if using internal cancellation
        if use_internal_cancellation:
            self.reset_cancellation()
            # Store metadata about the operation
            self.cancellation_manager.set_metadata("operation_type", "process_videos")
            self.cancellation_manager.set_metadata("file_count", len(video_files))

        # Helper function to check for cancellation
        def check_cancellation():
            # Check external cancellation function if provided
            if cancellation_check and cancellation_check():
                if progress_callback:
                    progress_callback("Processamento em lote cancelado pelo usuário (externo)", 0, len(video_files))
                error = AutoMeetAIError("Batch processing cancelled by user")
                error.user_friendly_message = "O processamento em lote foi cancelado pelo usuário."
                raise error

            # Check internal cancellation state if enabled
            if use_internal_cancellation and self.is_cancellation_requested():
                reason = self.cancellation_manager.get_cancellation_reason()
                if progress_callback:
                    message = f"Processamento em lote cancelado pelo usuário: {reason}" if reason else "Processamento em lote cancelado pelo usuário"
                    progress_callback(message, 0, len(video_files))
                error = AutoMeetAIError(f"Batch processing cancelled by user: {reason}" if reason else "Batch processing cancelled by user")
                error.user_friendly_message = f"O processamento em lote foi cancelado pelo usuário: {reason}" if reason else "O processamento em lote foi cancelado pelo usuário."
                raise error

        # Check for cancellation before starting
        check_cancellation()

        # Get parallel processing configuration
        if parallel_processing is None:
            parallel_processing = self.config_provider.get(
                "parallel_processing", DEFAULT_PARALLEL_PROCESSING
            )

        if max_workers is None:
            max_workers = self.config_provider.get(
                "max_workers", DEFAULT_MAX_WORKERS
            )

        if chunk_size is None:
            chunk_size = self.config_provider.get(
                "chunk_size_parallel", DEFAULT_CHUNK_SIZE_PARALLEL
            )

        results = {}
        errors = {}
        total_files = len(video_files)
        processed_count = 0

        # Use a thread-safe dictionary to store results from parallel processing
        from threading import Lock
        results_lock = Lock()

        self.logger.info(f"Starting batch processing of {total_files} files")
        if parallel_processing:
            self.logger.info(f"Using parallel processing with {max_workers} workers")
        else:
            self.logger.info("Using sequential processing")

        # Report initial progress
        if progress_callback:
            progress_callback("Iniciando processamento em lote", 0, total_files)

        # Helper function to check for cancellation
        def check_cancellation():
            if cancellation_check and cancellation_check():
                self.logger.info(f"Batch operation cancelled by user")
                raise AutoMeetAIError("Operação em lote cancelada pelo usuário")

        # Create a wrapper for the progress callback to handle both batch and individual file progress
        def batch_progress_wrapper(file_index: int, file_name: str) -> Optional[Callable]:
            if progress_callback is None:
                return None

            def wrapped_callback(stage: str, current: Union[int, float], total: Union[int, float]) -> None:
                # Calculate the overall progress as a combination of file index and file progress
                # Each file contributes 1 unit to the total progress
                file_progress = current / total if total > 0 else 0
                overall_progress = file_index + file_progress

                # Report both the individual file progress and the overall batch progress
                batch_stage = f"Arquivo {file_index + 1}/{total_files}: {stage}"
                progress_callback(batch_stage, overall_progress, total_files)

            return wrapped_callback

        # Worker function for processing a single file
        def process_file_worker(args):
            nonlocal processed_count
            i, video_file = args
            try:
                # Check for cancellation before starting the file
                if cancellation_check and cancellation_check():
                    return video_file, None, "Operation cancelled by user"

                # Report progress at the start of the file
                if progress_callback:
                    with results_lock:
                        progress_callback(
                            f"Processando arquivo {i + 1}/{total_files}: {os.path.basename(video_file)}", 
                            i, total_files
                        )

                self.logger.info(f"Processing file: {video_file}")

                # Create a progress callback wrapper for this specific file
                file_progress_callback = batch_progress_wrapper(i, video_file)

                result = self.process_video(
                    video_file=video_file,
                    transcription_config=transcription_config,
                    save_audio=save_audio,
                    allowed_video_extensions=allowed_video_extensions,
                    force_reprocess=force_reprocess,
                    output_format=output_format,
                    output_formats=output_formats,
                    format_options=format_options,
                    progress_callback=file_progress_callback,
                    cancellation_check=cancellation_check,
                    use_internal_cancellation=use_internal_cancellation
                )

                # Store the result in the shared dictionary
                with results_lock:
                    results[video_file] = result

                self.logger.info(f"Successfully processed file: {video_file}")

                # Report progress at the completion of the file
                if progress_callback:
                    with results_lock:
                        processed_count += 1
                        progress_callback(
                            f"Arquivo {i + 1}/{total_files} concluído ({processed_count}/{total_files})", 
                            processed_count, total_files
                        )

                return video_file, result, None  # Success

            except Exception as e:
                error_msg = f"Error processing file {video_file}: {e}"
                self.logger.error(error_msg)

                # Store the error in the shared dictionary
                with results_lock:
                    errors[video_file] = str(e)
                    results[video_file] = None

                    # Report error in progress
                    if progress_callback:
                        processed_count += 1
                        progress_callback(
                            f"Erro no arquivo {i + 1}/{total_files}: {os.path.basename(video_file)}", 
                            processed_count, total_files
                        )

                if not continue_on_error:
                    # Signal that processing should stop
                    return video_file, None, error_msg  # Error

                return video_file, None, None  # Error but continue

        # Process files either sequentially or in parallel
        if parallel_processing and total_files > 1:
            # Process files in parallel using ThreadPoolExecutor
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_file = {
                    executor.submit(process_file_worker, (i, video_file)): (i, video_file)
                    for i, video_file in enumerate(video_files)
                }

                # Process results as they complete
                for future in concurrent.futures.as_completed(future_to_file):
                    i, video_file = future_to_file[future]
                    try:
                        # Check for cancellation before processing the result
                        if cancellation_check and cancellation_check():
                            # Cancel all pending tasks
                            for f in future_to_file:
                                f.cancel()
                            if progress_callback:
                                progress_callback("Processamento em lote cancelado pelo usuário", i + 1, total_files)
                            error = AutoMeetAIError("Batch processing cancelled by user")
                            error.user_friendly_message = "O processamento em lote foi cancelado pelo usuário."
                            raise error

                        file, result, error_msg = future.result()

                        # If an error occurred and continue_on_error is False, cancel all pending tasks
                        if error_msg and not continue_on_error:
                            for f in future_to_file:
                                f.cancel()
                            if progress_callback:
                                progress_callback("Processamento em lote interrompido devido a erro", i + 1, total_files)
                            error = AutoMeetAIError(f"Batch processing stopped due to error: {error_msg}")
                            error.user_friendly_message = get_user_friendly_message(
                                f"O processamento em lote foi interrompido devido a um erro no arquivo '{video_file}': {error_msg}"
                            )
                            raise error

                    except Exception as e:
                        self.logger.error(f"Exception in worker thread for file {video_file}: {e}")
                        if not continue_on_error:
                            if progress_callback:
                                progress_callback("Processamento em lote interrompido devido a erro", i + 1, total_files)
                            error = AutoMeetAIError(f"Batch processing stopped due to error: {e}")
                            error.user_friendly_message = get_user_friendly_message(
                                f"O processamento em lote foi interrompido devido a um erro inesperado no arquivo '{video_file}': {e}"
                            )
                            raise error
        else:
            # Process files sequentially
            for i, video_file in enumerate(video_files):
                # Check for cancellation before processing each file
                if cancellation_check and cancellation_check():
                    if progress_callback:
                        progress_callback("Processamento em lote cancelado pelo usuário", i, total_files)
                    error = AutoMeetAIError("Batch processing cancelled by user")
                    error.user_friendly_message = "O processamento em lote foi cancelado pelo usuário."
                    raise error

                file, result, error_msg = process_file_worker((i, video_file))

                # If an error occurred and continue_on_error is False, stop processing
                if error_msg and not continue_on_error:
                    if progress_callback:
                        progress_callback("Processamento em lote interrompido devido a erro", i + 1, total_files)
                    error = AutoMeetAIError(f"Batch processing stopped due to error: {error_msg}")
                    error.user_friendly_message = get_user_friendly_message(
                        f"O processamento em lote foi interrompido devido a um erro no arquivo '{video_file}': {error_msg}"
                    )
                    raise error

        # Log summary of processing
        success_count = sum(1 for result in results.values() if result is not None)
        error_count = len(video_files) - success_count

        self.logger.info(f"Batch processing completed. Successful: {success_count}, Failed: {error_count}")

        if error_count > 0:
            self.logger.info("Files with errors:")
            for file, error in errors.items():
                self.logger.info(f"  - {file}: {error}")

        # Final progress report
        if progress_callback:
            progress_callback(f"Processamento em lote concluído. Sucesso: {success_count}, Falhas: {error_count}", 
                             total_files, total_files)

        return results

    def analyze_transcription(
        self, 
        transcription: TranscriptionResult, 
        system_prompt: str, 
        user_prompt_template: str,
        generation_options: Optional[Dict[str, Any]] = None,
        cancellation_check: Optional[Callable[[], bool]] = None,
        use_internal_cancellation: bool = True
    ) -> Optional[str]:
        """
        Analisa uma transcrição utilizando o serviço de geração de texto.

        Este método utiliza um modelo de linguagem para analisar o conteúdo de uma transcrição,
        gerando insights, resumos ou outras informações relevantes com base no texto transcrito.
        O processo envolve:
        1. Formatação do prompt do usuário com o texto da transcrição
        2. Envio dos prompts para o serviço de geração de texto
        3. Salvamento do resultado da análise em um arquivo

        O método utiliza o serviço de geração de texto fornecido durante a inicialização da classe,
        que pode ser uma implementação real ou uma implementação nula (seguindo o padrão Null Object).

        Para transcrições grandes, o método utiliza carregamento preguiçoso (lazy loading) para
        processar o texto em chunks, reduzindo o uso de memória.

        Args:
            transcription: O resultado da transcrição a ser analisado
            system_prompt: O prompt de sistema para o serviço de geração de texto
            user_prompt_template: Modelo para o prompt do usuário, que será formatado com o texto da transcrição
            generation_options: Configuração opcional para a geração de texto
            cancellation_check: Função opcional que retorna True se a operação deve ser cancelada.
                              Esta função é chamada em pontos-chave durante o processamento para verificar
                              se o usuário solicitou o cancelamento da operação.
            use_internal_cancellation: Indica se o gerenciador de cancelamento interno deve ser usado.
                                     Se True, o método também verificará o estado de cancelamento interno,
                                     permitindo que o cancelamento seja solicitado através do método
                                     request_cancellation().

        Returns:
            Optional[str]: O resultado da análise, ou None se a análise falhar

        Raises:
            ServiceError: Se houver um problema com o serviço de geração de texto
            FileError: Se houver um problema ao salvar a análise em um arquivo
            AutoMeetAIError: Para quaisquer outros erros específicos da aplicação
        """

        try:
            # Reset the cancellation state if using internal cancellation
            if use_internal_cancellation:
                self.reset_cancellation()
                # Store metadata about the operation
                self.cancellation_manager.set_metadata("operation_type", "analyze_transcription")
                self.cancellation_manager.set_metadata("audio_file", transcription.audio_file)

            # Helper function to check for cancellation
            def check_cancellation():
                # Check external cancellation function if provided
                if cancellation_check and cancellation_check():
                    self.logger.info(f"Analysis operation cancelled by user (external)")
                    raise AutoMeetAIError("Análise cancelada pelo usuário")

                # Check internal cancellation state if enabled
                if use_internal_cancellation and self.is_cancellation_requested():
                    reason = self.cancellation_manager.get_cancellation_reason()
                    self.logger.info(f"Analysis operation cancelled by user (internal), reason: {reason}")
                    raise AutoMeetAIError(f"Análise cancelada pelo usuário: {reason}" if reason else "Análise cancelada pelo usuário")

            # Check for cancellation at the beginning
            check_cancellation()

            # Check if we should use lazy text processing
            use_lazy_processing = self.config_provider.get(
                "use_lazy_text_processing", 
                DEFAULT_USE_LAZY_TEXT_PROCESSING
            )

            # Determine if this is a large transcription
            is_large_transcription = False
            if isinstance(transcription, OptimizedTranscriptionResult):
                # For OptimizedTranscriptionResult, check the utterance count
                is_large_transcription = transcription.get_utterance_count() > self.config_provider.get(
                    "large_transcription_threshold", 
                    DEFAULT_LARGE_TRANSCRIPTION_THRESHOLD
                )
            else:
                # For standard TranscriptionResult, check the utterance count
                is_large_transcription = len(transcription.utterances) > self.config_provider.get(
                    "large_transcription_threshold", 
                    DEFAULT_LARGE_TRANSCRIPTION_THRESHOLD
                )

            # Log the decision
            self.logger.info(f"Large transcription: {is_large_transcription}, Use lazy processing: {use_lazy_processing}")

            # Generate the analysis
            self.logger.info("Analyzing transcription...")

            if is_large_transcription and use_lazy_processing:
                # Use lazy text processing for large transcriptions
                self.logger.info("Using lazy text processing for large transcription")

                # Get configuration for lazy text processing
                chunk_size = self.config_provider.get(
                    "text_processing_chunk_size", 
                    DEFAULT_TEXT_PROCESSING_CHUNK_SIZE
                )

                max_chunks = self.config_provider.get(
                    "text_processing_max_chunks", 
                    DEFAULT_TEXT_PROCESSING_MAX_CHUNKS
                )

                # Create lazy text processor
                lazy_processor = LazyTextProcessor(chunk_size=chunk_size)

                # Define a function to process each chunk
                def process_chunk(chunk_text: str) -> str:
                    try:
                        # Check for cancellation before processing each chunk
                        check_cancellation()

                        # Format the user prompt with the chunk text
                        chunk_prompt = user_prompt_template.format(transcription=chunk_text)

                        # Generate analysis for this chunk
                        chunk_analysis = self.text_generation_service.generate(
                            system_prompt,
                            chunk_prompt,
                            generation_options
                        )

                        return chunk_analysis if chunk_analysis else ""
                    except Exception as e:
                        self.logger.error(f"Error processing chunk: {e}")
                        return f"[Erro ao processar este trecho: {e}]"

                # Process the transcription in chunks
                analysis = lazy_processor.process_transcription_in_chunks(
                    transcription=transcription,
                    processor_func=process_chunk,
                    max_chunks=max_chunks
                )

                if not analysis:
                    raise ServiceError("Text generation service returned empty result")
            else:
                # Use standard processing for small transcriptions
                try:
                    # Format the user prompt with the transcription text
                    user_prompt = user_prompt_template.format(transcription=transcription.to_formatted_text())
                except Exception as e:
                    raise ServiceError(f"Failed to format user prompt: {e}") from e

                try:
                    # Check for cancellation before generating analysis
                    check_cancellation()

                    # Generate analysis
                    analysis = self.text_generation_service.generate(
                        system_prompt,
                        user_prompt,
                        generation_options
                    )

                    if not analysis:
                        raise ServiceError("Text generation service returned empty result")
                except Exception as e:
                    if isinstance(e, ServiceError):
                        raise
                    raise ServiceError(f"Error during text generation: {e}") from e

            # Save the analysis to a file
            output_file = os.path.splitext(transcription.audio_file)[0] + "_analysis.txt"
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(analysis)
                self.logger.info(f"Analysis saved to {output_file}")
            except Exception as e:
                raise FileError(f"Failed to save analysis to file {output_file}: {e}") from e

            return analysis

        except AutoMeetAIError as e:
            # Log and re-raise application-specific exceptions with user-friendly message
            self.logger.error(f"{e.__class__.__name__}: {e}")
            # Add user-friendly message to the exception
            e.user_friendly_message = get_user_friendly_message(e, {
                'file_path': transcription.audio_file,
                'service_name': 'geração de texto'
            })
            raise
        except Exception as e:
            # Convert and log unexpected exceptions
            self.logger.error(f"Unexpected error analyzing transcription: {e}")
            error = AutoMeetAIError(f"Unexpected error analyzing transcription: {e}")
            error.user_friendly_message = get_user_friendly_message(e, {
                'file_path': transcription.audio_file,
                'service_name': 'geração de texto'
            })
            raise error from e
