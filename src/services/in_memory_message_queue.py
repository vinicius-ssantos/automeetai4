import threading
import queue
from typing import Any, Callable

from src.interfaces.message_queue import MessageQueue
from src.utils.logging import get_logger


class InMemoryMessageQueue(MessageQueue):
    """Fila de mensagens em memória para processamento assíncrono."""

    def __init__(self, handler: Callable[[Any], None], maxsize: int = 0) -> None:
        """Inicializa a fila.

        Args:
            handler: Função chamada para processar cada mensagem.
            maxsize: Tamanho máximo da fila (0 para ilimitado).
        """
        self._queue: queue.Queue[Any] = queue.Queue(maxsize=maxsize)
        self._handler = handler
        self._threads: list[threading.Thread] = []
        self._stop_event = threading.Event()
        self.logger = get_logger(__name__)

    def iniciar(self, num_workers: int = 1) -> None:
        """Inicia as threads de processamento."""
        for _ in range(num_workers):
            thread = threading.Thread(target=self._worker, daemon=True)
            thread.start()
            self._threads.append(thread)
        self.logger.info("Fila iniciada com %s workers", num_workers)

    def parar(self) -> None:
        """Sinaliza para as threads finalizarem e aguarda sua conclusão."""
        self._stop_event.set()
        for thread in self._threads:
            thread.join()
        self.logger.info("Fila parada")

    def publicar(self, mensagem: Any) -> None:
        """Adiciona uma mensagem na fila."""
        self._queue.put(mensagem)
        self.logger.debug("Mensagem enfileirada: %s", mensagem)

    def _worker(self) -> None:
        while not self._stop_event.is_set():
            try:
                mensagem = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                self._handler(mensagem)
            finally:
                self._queue.task_done()
