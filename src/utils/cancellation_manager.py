from threading import Event, Lock
from typing import Callable, Optional, Dict, Any
from src.utils.logging import get_logger

class CancellationManager:
    """
    Gerenciador de cancelamento para operações de longa duração.
    
    Esta classe fornece uma maneira centralizada de gerenciar o estado de cancelamento
    para operações de longa duração, permitindo que diferentes partes da aplicação
    verifiquem se uma operação foi cancelada.
    """
    
    # Inicializa o logger para esta classe
    logger = get_logger(__name__)
    
    def __init__(self):
        """
        Inicializa o gerenciador de cancelamento.
        """
        self._cancel_event = Event()
        self._lock = Lock()
        self._operation_metadata: Dict[str, Any] = {}
    
    def request_cancellation(self, reason: Optional[str] = None) -> None:
        """
        Solicita o cancelamento da operação atual.
        
        Args:
            reason: Motivo opcional para o cancelamento
        """
        with self._lock:
            if reason:
                self._operation_metadata["cancellation_reason"] = reason
                self.logger.info(f"Cancelamento solicitado: {reason}")
            else:
                self.logger.info("Cancelamento solicitado")
            self._cancel_event.set()
    
    def is_cancellation_requested(self) -> bool:
        """
        Verifica se o cancelamento foi solicitado.
        
        Returns:
            bool: True se o cancelamento foi solicitado, False caso contrário
        """
        return self._cancel_event.is_set()
    
    def get_cancellation_check(self) -> Callable[[], bool]:
        """
        Retorna uma função que verifica se o cancelamento foi solicitado.
        
        Esta função pode ser passada para métodos que aceitam um callback de verificação
        de cancelamento.
        
        Returns:
            Callable[[], bool]: Função que retorna True se o cancelamento foi solicitado
        """
        return lambda: self.is_cancellation_requested()
    
    def reset(self) -> None:
        """
        Reinicia o estado de cancelamento.
        
        Isso deve ser chamado antes de iniciar uma nova operação.
        """
        with self._lock:
            self._cancel_event.clear()
            self._operation_metadata.clear()
            self.logger.info("Estado de cancelamento reiniciado")
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Define metadados para a operação atual.
        
        Args:
            key: Chave do metadado
            value: Valor do metadado
        """
        with self._lock:
            self._operation_metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Obtém metadados da operação atual.
        
        Args:
            key: Chave do metadado
            default: Valor padrão a ser retornado se a chave não existir
            
        Returns:
            Any: Valor do metadado, ou o valor padrão se a chave não existir
        """
        with self._lock:
            return self._operation_metadata.get(key, default)
    
    def get_cancellation_reason(self) -> Optional[str]:
        """
        Obtém o motivo do cancelamento, se disponível.
        
        Returns:
            Optional[str]: Motivo do cancelamento, ou None se não houver motivo ou se
                          o cancelamento não foi solicitado
        """
        if not self.is_cancellation_requested():
            return None
        
        with self._lock:
            return self._operation_metadata.get("cancellation_reason")