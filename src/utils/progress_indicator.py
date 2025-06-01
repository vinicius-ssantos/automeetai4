"""
Utilitário para indicadores de progresso para operações de longa duração.

Este módulo fornece classes e funções para criar e gerenciar indicadores de progresso
para operações de longa duração, como processamento de vídeo, transcrição e análise.
"""

from typing import Optional, Callable, Union, Dict, Any, List
import time
import threading
from enum import Enum
from src.utils.logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)


class ProgressState(Enum):
    """
    Estados possíveis para um indicador de progresso.
    """
    NOT_STARTED = "not_started"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProgressIndicator:
    """
    Indicador de progresso para operações de longa duração.
    
    Esta classe fornece uma interface para reportar e monitorar o progresso
    de operações de longa duração, como processamento de vídeo, transcrição e análise.
    """
    
    def __init__(
        self, 
        total_steps: int = 100,
        description: str = "Operação em andamento",
        callback: Optional[Callable[[str, Union[int, float], Union[int, float], ProgressState], None]] = None
    ):
        """
        Inicializa o indicador de progresso.
        
        Args:
            total_steps: Número total de passos da operação
            description: Descrição da operação
            callback: Função de callback para reportar o progresso
                      Recebe quatro parâmetros: (1) descrição da etapa atual, 
                      (2) valor atual do progresso, (3) valor total/máximo do progresso,
                      (4) estado atual do progresso
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.callback = callback
        self.state = ProgressState.NOT_STARTED
        self.start_time = None
        self.end_time = None
        self.messages = []
        self._lock = threading.RLock()
        
    def start(self, description: Optional[str] = None) -> None:
        """
        Inicia o indicador de progresso.
        
        Args:
            description: Descrição opcional para substituir a descrição padrão
        """
        with self._lock:
            if description:
                self.description = description
                
            self.state = ProgressState.RUNNING
            self.start_time = time.time()
            self.current_step = 0
            
            self._report_progress("Iniciando operação")
            
    def update(self, step: Union[int, float], message: str) -> None:
        """
        Atualiza o progresso da operação.
        
        Args:
            step: Passo atual ou incremento no progresso
            message: Mensagem descrevendo o estado atual
        """
        with self._lock:
            if self.state != ProgressState.RUNNING:
                return
                
            # Se step for um incremento (menor que o total), adiciona ao passo atual
            if step < self.total_steps:
                self.current_step = min(self.total_steps, self.current_step + step)
            else:
                # Caso contrário, assume que é o valor absoluto do passo
                self.current_step = min(self.total_steps, step)
                
            self._report_progress(message)
            
    def complete(self, message: str = "Operação concluída com sucesso") -> None:
        """
        Marca a operação como concluída.
        
        Args:
            message: Mensagem de conclusão
        """
        with self._lock:
            self.current_step = self.total_steps
            self.state = ProgressState.COMPLETED
            self.end_time = time.time()
            
            self._report_progress(message)
            
    def fail(self, message: str = "Operação falhou") -> None:
        """
        Marca a operação como falha.
        
        Args:
            message: Mensagem de falha
        """
        with self._lock:
            self.state = ProgressState.FAILED
            self.end_time = time.time()
            
            self._report_progress(message)
            
    def cancel(self, message: str = "Operação cancelada pelo usuário") -> None:
        """
        Marca a operação como cancelada.
        
        Args:
            message: Mensagem de cancelamento
        """
        with self._lock:
            self.state = ProgressState.CANCELLED
            self.end_time = time.time()
            
            self._report_progress(message)
            
    def pause(self, message: str = "Operação pausada") -> None:
        """
        Pausa a operação.
        
        Args:
            message: Mensagem de pausa
        """
        with self._lock:
            if self.state == ProgressState.RUNNING:
                self.state = ProgressState.PAUSED
                
                self._report_progress(message)
                
    def resume(self, message: str = "Operação retomada") -> None:
        """
        Retoma a operação pausada.
        
        Args:
            message: Mensagem de retomada
        """
        with self._lock:
            if self.state == ProgressState.PAUSED:
                self.state = ProgressState.RUNNING
                
                self._report_progress(message)
                
    def get_progress(self) -> float:
        """
        Retorna o progresso atual como uma porcentagem.
        
        Returns:
            float: Progresso atual (0-100)
        """
        with self._lock:
            if self.total_steps == 0:
                return 0.0
                
            return (self.current_step / self.total_steps) * 100.0
            
    def get_elapsed_time(self) -> Optional[float]:
        """
        Retorna o tempo decorrido desde o início da operação.
        
        Returns:
            Optional[float]: Tempo decorrido em segundos, ou None se a operação não foi iniciada
        """
        with self._lock:
            if not self.start_time:
                return None
                
            end = self.end_time if self.end_time else time.time()
            return end - self.start_time
            
    def get_estimated_time_remaining(self) -> Optional[float]:
        """
        Estima o tempo restante para a conclusão da operação.
        
        Returns:
            Optional[float]: Tempo estimado restante em segundos, ou None se não for possível estimar
        """
        with self._lock:
            if not self.start_time or self.state != ProgressState.RUNNING:
                return None
                
            if self.current_step == 0:
                return None
                
            elapsed = time.time() - self.start_time
            progress_ratio = self.current_step / self.total_steps
            
            if progress_ratio == 0:
                return None
                
            total_estimated = elapsed / progress_ratio
            remaining = total_estimated - elapsed
            
            return max(0, remaining)
            
    def get_status(self) -> Dict[str, Any]:
        """
        Retorna o status atual do indicador de progresso.
        
        Returns:
            Dict[str, Any]: Status atual com informações detalhadas
        """
        with self._lock:
            elapsed = self.get_elapsed_time()
            remaining = self.get_estimated_time_remaining()
            
            return {
                "description": self.description,
                "current_step": self.current_step,
                "total_steps": self.total_steps,
                "progress_percent": self.get_progress(),
                "state": self.state.value,
                "elapsed_time": elapsed,
                "estimated_time_remaining": remaining,
                "messages": self.messages[-5:] if self.messages else []  # Últimas 5 mensagens
            }
            
    def _report_progress(self, message: str) -> None:
        """
        Reporta o progresso atual através do callback e registra a mensagem.
        
        Args:
            message: Mensagem descrevendo o estado atual
        """
        # Adiciona a mensagem ao histórico
        timestamp = time.time()
        self.messages.append({
            "time": timestamp,
            "message": message,
            "progress": self.current_step,
            "state": self.state.value
        })
        
        # Limita o histórico de mensagens
        if len(self.messages) > 100:
            self.messages = self.messages[-100:]
            
        # Registra no log
        logger.info(f"Progresso ({self.get_progress():.1f}%): {message}")
        
        # Chama o callback se fornecido
        if self.callback:
            try:
                self.callback(message, self.current_step, self.total_steps, self.state)
            except Exception as e:
                logger.error(f"Erro ao chamar callback de progresso: {e}")


class ProgressManager:
    """
    Gerenciador de múltiplos indicadores de progresso.
    
    Esta classe permite gerenciar múltiplos indicadores de progresso
    para diferentes operações simultâneas.
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls) -> 'ProgressManager':
        """
        Retorna a instância singleton do gerenciador de progresso.
        
        Returns:
            ProgressManager: Instância do gerenciador
        """
        if cls._instance is None:
            cls._instance = ProgressManager()
        return cls._instance
    
    def __init__(self):
        """
        Inicializa o gerenciador de progresso.
        """
        self.indicators = {}
        self._lock = threading.RLock()
        
    def create_indicator(
        self, 
        operation_id: str,
        total_steps: int = 100,
        description: str = "Operação em andamento",
        callback: Optional[Callable[[str, Union[int, float], Union[int, float], ProgressState], None]] = None
    ) -> ProgressIndicator:
        """
        Cria um novo indicador de progresso.
        
        Args:
            operation_id: Identificador único da operação
            total_steps: Número total de passos da operação
            description: Descrição da operação
            callback: Função de callback para reportar o progresso
            
        Returns:
            ProgressIndicator: O indicador de progresso criado
        """
        with self._lock:
            indicator = ProgressIndicator(total_steps, description, callback)
            self.indicators[operation_id] = indicator
            return indicator
            
    def get_indicator(self, operation_id: str) -> Optional[ProgressIndicator]:
        """
        Retorna um indicador de progresso existente.
        
        Args:
            operation_id: Identificador único da operação
            
        Returns:
            Optional[ProgressIndicator]: O indicador de progresso, ou None se não existir
        """
        with self._lock:
            return self.indicators.get(operation_id)
            
    def remove_indicator(self, operation_id: str) -> None:
        """
        Remove um indicador de progresso.
        
        Args:
            operation_id: Identificador único da operação
        """
        with self._lock:
            if operation_id in self.indicators:
                del self.indicators[operation_id]
                
    def get_all_indicators(self) -> Dict[str, ProgressIndicator]:
        """
        Retorna todos os indicadores de progresso ativos.
        
        Returns:
            Dict[str, ProgressIndicator]: Dicionário mapeando IDs para indicadores
        """
        with self._lock:
            return self.indicators.copy()
            
    def get_all_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna o status de todos os indicadores de progresso ativos.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dicionário mapeando IDs para status
        """
        with self._lock:
            return {op_id: indicator.get_status() for op_id, indicator in self.indicators.items()}


def create_progress_callback(
    indicator: ProgressIndicator
) -> Callable[[str, Union[int, float], Union[int, float]], None]:
    """
    Cria uma função de callback compatível com a interface existente do AutoMeetAI.
    
    Args:
        indicator: O indicador de progresso a ser atualizado
        
    Returns:
        Callable: Função de callback compatível com AutoMeetAI
    """
    def callback(message: str, current: Union[int, float], total: Union[int, float]) -> None:
        # Calcula o progresso relativo ao total de passos do indicador
        if total > 0:
            progress = (current / total) * indicator.total_steps
            indicator.update(progress, message)
        else:
            indicator.update(current, message)
    
    return callback