from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Union, Callable, Generator, BinaryIO

from src.models.transcription_result import TranscriptionResult


class StreamingTranscriptionService(ABC):
    """
    Interface para serviços de transcrição de áudio em tempo real.
    Seguindo o Princípio da Segregação de Interface, esta interface define
    apenas os métodos necessários para transcrição de áudio em streaming.
    """

    @abstractmethod
    def start_streaming(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Inicia uma sessão de transcrição em streaming.

        Args:
            config: Parâmetros de configuração opcionais para a transcrição

        Returns:
            bool: True se a sessão foi iniciada com sucesso, False caso contrário
        """
        pass

    @abstractmethod
    def transcribe_chunk(self, audio_chunk: bytes) -> Optional[Dict[str, Any]]:
        """
        Transcreve um fragmento de áudio em tempo real.

        Args:
            audio_chunk: Fragmento de áudio em bytes para transcrever

        Returns:
            Optional[Dict[str, Any]]: Resultado parcial da transcrição, ou None se falhou
        """
        pass

    @abstractmethod
    def stop_streaming(self) -> Optional[TranscriptionResult]:
        """
        Finaliza a sessão de transcrição em streaming e retorna o resultado completo.

        Returns:
            Optional[TranscriptionResult]: O resultado completo da transcrição, ou None se falhou
        """
        pass

    @abstractmethod
    def is_streaming(self) -> bool:
        """
        Verifica se uma sessão de streaming está ativa.

        Returns:
            bool: True se uma sessão de streaming está ativa, False caso contrário
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass
