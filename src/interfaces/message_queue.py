from abc import ABC, abstractmethod
from typing import Any


class MessageQueue(ABC):
    """Interface para filas de mensagens assíncronas."""

    @abstractmethod
    def iniciar(self, num_workers: int = 1) -> None:
        """Inicia os workers da fila."""

    @abstractmethod
    def parar(self) -> None:
        """Encerra o processamento da fila."""

    @abstractmethod
    def publicar(self, mensagem: Any) -> None:
        """Enfileira uma nova mensagem."""
