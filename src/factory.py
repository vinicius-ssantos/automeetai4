from typing import Optional, Dict, Any, List, Type
from src.config.env_config_provider import EnvConfigProvider
from src.config.user_preferences_provider import UserPreferencesProvider
from src.config.composite_config_provider import CompositeConfigProvider
from src.services.moviepy_audio_converter import MoviePyAudioConverter
from src.services.assemblyai_transcription_service import AssemblyAITranscriptionService
from src.services.mock_transcription_service import MockTranscriptionService
from src.services.whisper_transcription_service import WhisperTranscriptionService
from src.services.openai_text_generation_service import OpenAITextGenerationService
from src.services.null_text_generation_service import NullTextGenerationService
from src.automeetai import AutoMeetAI
from src.interfaces.factory import AutoMeetAIFactoryInterface
from src.interfaces.transcription_service import TranscriptionService
from src.interfaces.plugin import PluginRegistry, Plugin
from src.container import Container
from src.utils.logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)


class AutoMeetAIFactory(AutoMeetAIFactoryInterface):
    """
    Classe fábrica para criar instâncias do AutoMeetAI.

    Seguindo o Padrão Factory, esta classe é responsável por criar e configurar
    objetos complexos, encapsulando a lógica de inicialização e configuração
    dos componentes necessários para o funcionamento da aplicação.

    Esta implementação utiliza um contêiner de injeção de dependência para
    gerenciar os serviços e suas dependências, facilitando a extensibilidade
    e testabilidade da aplicação.
    """

    def __init__(self):
        """
        Inicializa a fábrica com um contêiner de injeção de dependência.

        Este método cria uma nova instância do contêiner de injeção de dependência
        que será usado para registrar e resolver os serviços necessários para
        a criação de instâncias do AutoMeetAI.
        """
        self.container = Container()
        self.plugin_registry = PluginRegistry()
        self.plugins_loaded = False
        self.plugin_config = {}

    def load_plugins(self, plugin_dir: str = "plugins") -> int:
        """
        Carrega plugins do diretório especificado.

        Este método utiliza o PluginRegistry para descobrir e carregar plugins
        do diretório especificado. Os plugins carregados podem fornecer implementações
        alternativas para os serviços utilizados pela aplicação.

        Args:
            plugin_dir: Diretório onde procurar plugins

        Returns:
            int: Número de plugins carregados
        """
        count = self.plugin_registry.discover_plugins(plugin_dir)
        self.plugins_loaded = count > 0
        return count

    def configure_plugins(self, plugin_config: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """
        Configura os plugins carregados com as configurações fornecidas.

        Este método inicializa os plugins carregados com suas respectivas configurações.
        As configurações são armazenadas para uso posterior na criação de instâncias do AutoMeetAI.

        Args:
            plugin_config: Dicionário mapeando nomes de plugins para suas configurações

        Returns:
            Dict[str, bool]: Dicionário mapeando nomes de plugins para status de inicialização
        """
        self.plugin_config = plugin_config
        return self.plugin_registry.initialize_plugins(plugin_config)

    def get_plugin_names(self) -> List[str]:
        """
        Retorna os nomes dos plugins carregados.

        Returns:
            List[str]: Lista de nomes dos plugins carregados
        """
        return [plugin.name for plugin in self.plugin_registry.get_plugins()]

    def get_plugin_info(self) -> List[Dict[str, str]]:
        """
        Retorna informações sobre os plugins carregados.

        Returns:
            List[Dict[str, str]]: Lista de dicionários contendo informações sobre os plugins
        """
        return [
            {
                "name": plugin.name,
                "version": plugin.version,
                "description": plugin.description,
                "extension_points": ", ".join(plugin.get_extension_points())
            }
            for plugin in self.plugin_registry.get_plugins()
        ]

    def create(
        self,
        assemblyai_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        include_text_generation: bool = True,
        use_cache: bool = True,
        cache_dir: str = "cache",
        use_plugins: bool = True,
        plugin_preferences: Optional[Dict[str, str]] = None,
        transcription_service_type: str = "assemblyai",
        use_user_preferences: bool = True,
        user_preferences_file: str = "user_preferences.json",
        use_message_queue: bool = False,
        queue_workers: int = 1
    ) -> AutoMeetAI:
        """
        Cria uma nova instância do AutoMeetAI com todas as dependências necessárias.

        Este método implementa o padrão Factory Method, encapsulando a lógica complexa
        de criação e configuração de objetos. Ele realiza as seguintes etapas:
        1. Cria e configura um provedor de configuração
        2. Registra os serviços necessários no contêiner de injeção de dependência
        3. Resolve as dependências do contêiner
        4. Cria e retorna uma instância configurada do AutoMeetAI

        As chaves de API podem ser fornecidas diretamente como parâmetros ou através
        de variáveis de ambiente (AUTOMEETAI_ASSEMBLYAI_API_KEY e AUTOMEETAI_OPENAI_API_KEY).

        Args:
            assemblyai_api_key: Chave de API para o serviço AssemblyAI
            openai_api_key: Chave de API para o serviço OpenAI
            include_text_generation: Indica se o serviço de geração de texto deve ser incluído
            use_cache: Indica se o cache de transcrições deve ser utilizado
            cache_dir: Diretório para armazenar os arquivos de cache
            use_plugins: Indica se os plugins devem ser utilizados
            plugin_preferences: Dicionário mapeando pontos de extensão para nomes de plugins preferidos
            transcription_service_type: Tipo de serviço de transcrição a ser utilizado ("assemblyai", "whisper" ou "mock")
            use_user_preferences: Indica se as preferências do usuário devem ser utilizadas
            user_preferences_file: Caminho para o arquivo de preferências do usuário
            use_message_queue: Se True, inicializa uma fila de mensagens para processamento assíncrono
            queue_workers: Número de workers para a fila de mensagens

        Returns:
            AutoMeetAI: Uma instância configurada do AutoMeetAI
        """
        # Create configuration providers
        env_config_provider = EnvConfigProvider()

        # Create a composite config provider
        composite_provider = CompositeConfigProvider()

        # Add environment config provider first (highest precedence)
        composite_provider.add_provider(env_config_provider)

        # Add user preferences provider if enabled
        if use_user_preferences:
            user_preferences_provider = UserPreferencesProvider(user_preferences_file)
            composite_provider.add_provider(user_preferences_provider)
            logger.info(f"Usando preferências do usuário do arquivo: {user_preferences_file}")

        # Set API keys if provided
        if assemblyai_api_key:
            composite_provider.set("assemblyai_api_key", assemblyai_api_key)

        if openai_api_key:
            composite_provider.set("openai_api_key", openai_api_key)

        # Register services in the container
        self.container.register_instance("config_provider", composite_provider)

        # Assign composite_provider to config_provider for use in resolving services
        config_provider = composite_provider

        # Initialize plugin preferences if not provided
        if plugin_preferences is None:
            plugin_preferences = {}

        # Check if we should use plugins and if any are loaded
        use_plugin_implementations = use_plugins and self.plugins_loaded

        # Dictionary to store the services we'll use
        services = {
            "audio_converter": None,
            "transcription_service": None,
            "text_generation_service": None
        }

        # If using plugins, try to get implementations from plugins first
        if use_plugin_implementations:
            for extension_point in services.keys():
                # Check if there's a preferred plugin for this extension point
                preferred_plugin = plugin_preferences.get(extension_point)

                if preferred_plugin:
                    # Try to get the implementation from the preferred plugin
                    implementation = self.plugin_registry.get_implementation(extension_point, preferred_plugin)
                    if implementation:
                        services[extension_point] = implementation
                else:
                    # If no preferred plugin, get all plugins for this extension point
                    plugins = self.plugin_registry.get_plugins_for_extension_point(extension_point)
                    if plugins:
                        # Use the first available plugin
                        implementation = plugins[0].get_implementation(extension_point)
                        if implementation:
                            services[extension_point] = implementation

        # Register default implementations for services not provided by plugins
        if services["audio_converter"] is None:
            self.container.register("audio_converter", MoviePyAudioConverter)
            services["audio_converter"] = self.container.resolve("audio_converter", config_provider=config_provider)

        if services["transcription_service"] is None:
            # Select the transcription service based on the specified type
            transcription_service_class: Type[TranscriptionService]

            if transcription_service_type.lower() == "mock":
                transcription_service_class = MockTranscriptionService
            elif transcription_service_type.lower() == "assemblyai":
                transcription_service_class = AssemblyAITranscriptionService
            elif transcription_service_type.lower() == "whisper":
                transcription_service_class = WhisperTranscriptionService
            else:
                # Default to AssemblyAI if an unknown type is specified
                self.logger.warning(f"Unknown transcription service type: {transcription_service_type}. Using AssemblyAI.")
                transcription_service_class = AssemblyAITranscriptionService

            self.container.register("transcription_service", transcription_service_class)
            services["transcription_service"] = self.container.resolve("transcription_service", config_provider=config_provider)

        if services["text_generation_service"] is None:
            if include_text_generation:
                self.container.register("text_generation_service", OpenAITextGenerationService)
                services["text_generation_service"] = self.container.resolve("text_generation_service", config_provider=config_provider)
            else:
                services["text_generation_service"] = NullTextGenerationService()

        # Create the application
        app = AutoMeetAI(
            config_provider=config_provider,
            audio_converter=services["audio_converter"],
            transcription_service=services["transcription_service"],
            text_generation_service=services["text_generation_service"],
            use_cache=use_cache,
            cache_dir=cache_dir
        )

        # Configure message queue if requested
        if use_message_queue:
            from src.services.in_memory_message_queue import InMemoryMessageQueue

            queue = InMemoryMessageQueue(lambda path: app.process_video(path))
            app.set_message_queue(queue)
            app.iniciar_fila(queue_workers)

        return app
