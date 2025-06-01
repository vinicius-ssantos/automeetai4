from abc import ABC, abstractmethod
from typing import Dict, Any, List, Type, Optional

class Plugin(ABC):
    """
    Interface base para plugins do AutoMeetAI.
    
    Esta interface define o contrato que todos os plugins devem implementar.
    Seguindo o Princípio da Interface Segregada, esta interface define apenas
    os métodos essenciais que todos os plugins devem fornecer.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Retorna o nome do plugin.
        
        Returns:
            str: Nome único do plugin
        """
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """
        Retorna a versão do plugin.
        
        Returns:
            str: Versão do plugin no formato semântico (ex: "1.0.0")
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Retorna uma descrição do plugin.
        
        Returns:
            str: Descrição detalhada do plugin e suas funcionalidades
        """
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Inicializa o plugin com a configuração fornecida.
        
        Args:
            config: Dicionário contendo a configuração do plugin
            
        Returns:
            bool: True se a inicialização foi bem-sucedida, False caso contrário
        """
        pass
    
    @abstractmethod
    def get_extension_points(self) -> List[str]:
        """
        Retorna a lista de pontos de extensão que este plugin implementa.
        
        Os pontos de extensão possíveis incluem:
        - "audio_converter": Para conversores de áudio
        - "transcription_service": Para serviços de transcrição
        - "text_generation_service": Para serviços de geração de texto
        - "output_formatter": Para formatadores de saída
        
        Returns:
            List[str]: Lista de pontos de extensão implementados por este plugin
        """
        pass
    
    @abstractmethod
    def get_implementation(self, extension_point: str) -> Optional[Any]:
        """
        Retorna a implementação do plugin para o ponto de extensão especificado.
        
        Args:
            extension_point: Nome do ponto de extensão
            
        Returns:
            Optional[Any]: A implementação do ponto de extensão ou None se não suportado
        """
        pass


class PluginRegistry:
    """
    Registro de plugins do AutoMeetAI.
    
    Esta classe é responsável por descobrir, registrar e gerenciar plugins.
    Segue o padrão Singleton para garantir um único registro de plugins em toda a aplicação.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PluginRegistry, cls).__new__(cls)
            cls._instance._plugins = {}
            cls._instance._extension_points = {
                "audio_converter": [],
                "transcription_service": [],
                "text_generation_service": [],
                "output_formatter": []
            }
            cls._instance._initialized = False
        return cls._instance
    
    def register_plugin(self, plugin: Plugin) -> bool:
        """
        Registra um plugin no sistema.
        
        Args:
            plugin: Instância do plugin a ser registrado
            
        Returns:
            bool: True se o registro foi bem-sucedido, False caso contrário
        """
        if plugin.name in self._plugins:
            return False
        
        self._plugins[plugin.name] = plugin
        
        # Registra o plugin em seus pontos de extensão
        for ext_point in plugin.get_extension_points():
            if ext_point in self._extension_points:
                self._extension_points[ext_point].append(plugin)
        
        return True
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """
        Obtém um plugin pelo nome.
        
        Args:
            name: Nome do plugin
            
        Returns:
            Optional[Plugin]: O plugin solicitado ou None se não encontrado
        """
        return self._plugins.get(name)
    
    def get_plugins(self) -> List[Plugin]:
        """
        Retorna todos os plugins registrados.
        
        Returns:
            List[Plugin]: Lista de todos os plugins registrados
        """
        return list(self._plugins.values())
    
    def get_plugins_for_extension_point(self, extension_point: str) -> List[Plugin]:
        """
        Retorna todos os plugins que implementam um determinado ponto de extensão.
        
        Args:
            extension_point: Nome do ponto de extensão
            
        Returns:
            List[Plugin]: Lista de plugins que implementam o ponto de extensão
        """
        if extension_point not in self._extension_points:
            return []
        
        return self._extension_points[extension_point]
    
    def get_implementation(self, extension_point: str, plugin_name: str) -> Optional[Any]:
        """
        Obtém a implementação de um ponto de extensão de um plugin específico.
        
        Args:
            extension_point: Nome do ponto de extensão
            plugin_name: Nome do plugin
            
        Returns:
            Optional[Any]: A implementação ou None se não encontrada
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            return None
        
        return plugin.get_implementation(extension_point)
    
    def discover_plugins(self, plugin_dir: str = "plugins") -> int:
        """
        Descobre e carrega plugins de um diretório.
        
        Args:
            plugin_dir: Diretório onde procurar plugins
            
        Returns:
            int: Número de plugins descobertos e carregados
        """
        import os
        import importlib.util
        import sys
        
        count = 0
        
        # Garante que o diretório existe
        if not os.path.exists(plugin_dir):
            os.makedirs(plugin_dir)
        
        # Adiciona o diretório de plugins ao path
        if plugin_dir not in sys.path:
            sys.path.append(plugin_dir)
        
        # Procura por arquivos Python no diretório de plugins
        for filename in os.listdir(plugin_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]  # Remove a extensão .py
                module_path = os.path.join(plugin_dir, filename)
                
                try:
                    # Carrega o módulo
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Procura por classes que herdam de Plugin
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and issubclass(attr, Plugin) and attr != Plugin:
                            try:
                                # Instancia o plugin
                                plugin = attr()
                                if self.register_plugin(plugin):
                                    count += 1
                            except Exception as e:
                                print(f"Erro ao instanciar plugin {attr_name}: {e}")
                
                except Exception as e:
                    print(f"Erro ao carregar plugin {module_name}: {e}")
        
        return count
    
    def initialize_plugins(self, config: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """
        Inicializa todos os plugins registrados com suas configurações.
        
        Args:
            config: Dicionário mapeando nomes de plugins para suas configurações
            
        Returns:
            Dict[str, bool]: Dicionário mapeando nomes de plugins para status de inicialização
        """
        results = {}
        
        for name, plugin in self._plugins.items():
            plugin_config = config.get(name, {})
            try:
                success = plugin.initialize(plugin_config)
                results[name] = success
            except Exception as e:
                print(f"Erro ao inicializar plugin {name}: {e}")
                results[name] = False
        
        self._initialized = True
        return results