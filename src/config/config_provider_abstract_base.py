from abc import ABC, abstractmethod
from typing import Any, Optional


class ConfigProvider(ABC):
    """
    Interface para provedores de configuração.

    Segue o Princípio da Inversão de Dependência: módulos de alto nível dependem
    de abstrações, não de implementações concretas.
    """

    @abstractmethod
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Recupera um valor de configuração.
        """
        raise NotImplementedError

    # ↓  deixa de ser @abstractmethod: uma implementação padrão simples
    def set(self, key: str, value: Any) -> None:  # noqa: D401
        """
        Define um valor de configuração.

        Implementação padrão apenas lança NotImplementedError para indicar
        que o provedor pode ser somente-leitura. Classes que realmente precisam
        persistir valores devem sobrescrever este método.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} é somente-leitura: método 'set' não implementado."
        )