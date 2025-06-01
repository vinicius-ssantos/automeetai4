from typing import Dict, Type, Any, Optional, TypeVar, Generic, cast

T = TypeVar('T')

class Container:
    """
    Container de injeção de dependência simples.
    Gerencia o ciclo de vida dos serviços e suas dependências.
    """

    def __init__(self):
        """
        Inicializa o container com dicionários vazios para registros e instâncias.
        """
        self._registrations: Dict[str, Type[Any]] = {}
        self._instances: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}

    def register(self, name: str, cls: Type[T]) -> None:
        """
        Registra uma classe no container.

        Args:
            name: Nome para registrar a classe
            cls: A classe a ser registrada
        """
        self._registrations[name] = cls

    def register_instance(self, name: str, instance: T) -> None:
        """
        Registra uma instância existente no container.

        Args:
            name: Nome para registrar a instância
            instance: A instância a ser registrada
        """
        self._instances[name] = instance

    def register_factory(self, name: str, factory: callable) -> None:
        """
        Registra uma fábrica para criar instâncias sob demanda.

        Args:
            name: Nome para registrar a fábrica
            factory: Função de fábrica que cria a instância
        """
        self._factories[name] = factory

    def resolve(self, name: str, **kwargs) -> T:
        """
        Resolve uma dependência pelo nome.

        Args:
            name: Nome da dependência a ser resolvida
            **kwargs: Argumentos adicionais para passar para o construtor

        Returns:
            A instância resolvida

        Raises:
            KeyError: Se a dependência não estiver registrada
        """
        # Verificar se já temos uma instância
        if name in self._instances:
            return self._instances[name]

        # Verificar se temos uma fábrica
        if name in self._factories:
            instance = self._factories[name](**kwargs)
            self._instances[name] = instance
            return instance

        # Verificar se temos um registro de classe
        if name in self._registrations:
            cls = self._registrations[name]
            instance = cls(**kwargs)
            self._instances[name] = instance
            return instance

        raise KeyError(f"Dependência '{name}' não registrada no container")

    def get(self, name: str, default: Optional[T] = None) -> Optional[T]:
        """
        Obtém uma dependência pelo nome, retornando um valor padrão se não encontrada.

        Args:
            name: Nome da dependência a ser obtida
            default: Valor padrão a retornar se a dependência não for encontrada

        Returns:
            A instância resolvida ou o valor padrão
        """
        try:
            return self.resolve(name)
        except KeyError:
            return default
