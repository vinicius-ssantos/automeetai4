import os
import json
from typing import Any, Optional, Dict, Callable
from src.interfaces.config_provider import ConfigProvider
from src.config.config_validator import ConfigValidator
from src.utils.logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)


class UserPreferencesProvider(ConfigProvider):
    """
    Provedor de configuração que armazena preferências do usuário em um arquivo JSON.
    
    Seguindo o Princípio da Responsabilidade Única, esta classe é responsável apenas
    por fornecer valores de configuração baseados nas preferências do usuário.
    """

    def __init__(self, preferences_file: str = "user_preferences.json"):
        """
        Inicializa o provedor de preferências do usuário.
        
        Args:
            preferences_file: Caminho para o arquivo de preferências
        """
        self.preferences_file = preferences_file
        self._preferences: Dict[str, Any] = {}
        self._validators: Dict[str, Callable] = {
            # Configurações de transcrição
            "language_code": ConfigValidator.validate_language_code,
            "speakers_expected": ConfigValidator.validate_speakers_expected,
            
            # Configurações de modelo
            "openai_model": lambda model: ConfigValidator.validate_model_name(model, ["gpt-3.5-turbo", "gpt-4", "gpt-4o", "gpt-4o-2024-08-06"]),
            
            # Diretórios
            "output_directory": lambda dir: ConfigValidator.validate_directory(dir, create_if_missing=True)
        }
        
        # Carrega as preferências do arquivo, se existir
        self._load_preferences()
    
    def _load_preferences(self) -> None:
        """
        Carrega as preferências do arquivo.
        """
        if os.path.exists(self.preferences_file):
            try:
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    self._preferences = json.load(f)
                logger.info(f"Preferências do usuário carregadas de {self.preferences_file}")
            except Exception as e:
                logger.error(f"Erro ao carregar preferências do usuário: {e}")
                self._preferences = {}
    
    def _save_preferences(self) -> None:
        """
        Salva as preferências no arquivo.
        """
        try:
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(self._preferences, f, indent=4)
            logger.info(f"Preferências do usuário salvas em {self.preferences_file}")
        except Exception as e:
            logger.error(f"Erro ao salvar preferências do usuário: {e}")
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Obtém um valor de configuração pela chave.
        
        Args:
            key: A chave de configuração
            default: Valor padrão a ser retornado se a chave não for encontrada
            
        Returns:
            Any: O valor de configuração
        """
        # Verifica se a chave existe nas preferências
        if key in self._preferences:
            value = self._preferences[key]
            
            # Valida o valor se existir um validador para esta chave
            if key in self._validators:
                try:
                    return self._validators[key](value)
                except ValueError as e:
                    logger.warning(f"Valor de configuração inválido para {key}: {e}")
                    # Retorna o valor original se a validação falhar
                    return value
            
            return value
        
        # Retorna o valor padrão se a chave não for encontrada
        return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Define um valor de configuração e salva no arquivo de preferências.
        
        Args:
            key: A chave de configuração
            value: O valor de configuração
        """
        # Valida o valor se existir um validador para esta chave
        if key in self._validators:
            try:
                value = self._validators[key](value)
            except ValueError as e:
                logger.warning(f"Valor de configuração inválido para {key}: {e}")
                # Continua com o valor original se a validação falhar
        
        # Atualiza as preferências
        self._preferences[key] = value
        
        # Salva as preferências no arquivo
        self._save_preferences()
    
    def get_all(self) -> Dict[str, Any]:
        """
        Obtém todas as preferências do usuário.
        
        Returns:
            Dict[str, Any]: Todas as preferências do usuário
        """
        return self._preferences.copy()
    
    def clear(self) -> None:
        """
        Limpa todas as preferências do usuário.
        """
        self._preferences = {}
        self._save_preferences()