from typing import Any, Optional, Dict, List
from src.interfaces.config_provider import ConfigProvider
from src.utils.logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)


class CompositeConfigProvider(ConfigProvider):
    """
    Provedor de configuração composto que combina múltiplos provedores de configuração.
    
    Este provedor segue o padrão Composite, permitindo que múltiplos provedores
    de configuração sejam tratados como um único provedor. Ao buscar um valor,
    os provedores são consultados na ordem em que foram adicionados, e o primeiro
    valor encontrado é retornado.
    
    Isso permite combinar diferentes fontes de configuração, como variáveis de ambiente,
    preferências do usuário, arquivos de configuração, etc., com uma ordem de precedência
    clara.
    """
    
    def __init__(self, providers: Optional[List[ConfigProvider]] = None):
        """
        Inicializa o provedor de configuração composto.
        
        Args:
            providers: Lista de provedores de configuração a serem combinados
        """
        self.providers = providers or []
        
    def add_provider(self, provider: ConfigProvider) -> None:
        """
        Adiciona um provedor de configuração à lista de provedores.
        
        Os provedores são consultados na ordem em que foram adicionados,
        então os provedores adicionados primeiro têm maior precedência.
        
        Args:
            provider: Provedor de configuração a ser adicionado
        """
        self.providers.append(provider)
        
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Obtém um valor de configuração pela chave.
        
        Consulta cada provedor na ordem em que foram adicionados e retorna
        o primeiro valor encontrado. Se nenhum provedor tiver a chave,
        retorna o valor padrão.
        
        Args:
            key: A chave de configuração
            default: Valor padrão a ser retornado se a chave não for encontrada
            
        Returns:
            Any: O valor de configuração
        """
        # Se não houver provedores, retorna o valor padrão
        if not self.providers:
            return default
            
        # Consulta cada provedor na ordem
        for provider in self.providers:
            value = provider.get(key, None)
            if value is not None:
                return value
                
        # Se nenhum provedor tiver a chave, retorna o valor padrão
        return default
        
    def set(self, key: str, value: Any) -> None:
        """
        Define um valor de configuração em todos os provedores.
        
        Args:
            key: A chave de configuração
            value: O valor de configuração
        """
        # Se não houver provedores, não faz nada
        if not self.providers:
            logger.warning("Nenhum provedor de configuração disponível para definir o valor")
            return
            
        # Define o valor em todos os provedores
        for provider in self.providers:
            provider.set(key, value)
            
    def get_all(self) -> Dict[str, Any]:
        """
        Obtém todas as configurações de todos os provedores.
        
        Combina as configurações de todos os provedores, com os provedores
        adicionados primeiro tendo precedência em caso de chaves duplicadas.
        
        Returns:
            Dict[str, Any]: Todas as configurações combinadas
        """
        # Se não houver provedores, retorna um dicionário vazio
        if not self.providers:
            return {}
            
        # Combina as configurações de todos os provedores
        all_configs = {}
        
        # Itera pelos provedores na ordem inversa para que os primeiros
        # tenham precedência (sobrescrevam os valores dos últimos)
        for provider in reversed(self.providers):
            # Verifica se o provedor tem o método get_all
            if hasattr(provider, 'get_all') and callable(getattr(provider, 'get_all')):
                all_configs.update(provider.get_all())
                
        return all_configs