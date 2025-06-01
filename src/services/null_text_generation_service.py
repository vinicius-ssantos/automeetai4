from typing import Optional, Dict, Any

from src.interfaces.text_generation_service import TextGenerationService
from src.utils.logging import get_logger


class NullTextGenerationService(TextGenerationService):
    """
    Implementação nula do TextGenerationService seguindo o padrão Null Object.
    
    Esta classe implementa a interface TextGenerationService, mas não realiza
    nenhuma operação real. Ela é usada quando o serviço de geração de texto
    não está disponível ou não é necessário, eliminando a necessidade de
    verificações de nulo no código cliente.
    
    Seguindo o padrão Null Object, esta classe fornece uma implementação
    "neutra" que não causa erros quando seus métodos são chamados.
    """
    
    # Initialize logger for this class
    logger = get_logger(__name__)
    
    def __init__(self):
        """
        Inicializa o serviço nulo de geração de texto.
        """
        self.logger.info("Initializing NullTextGenerationService")
    
    def generate(self, system_prompt: str, user_prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Implementação nula do método de geração de texto.
        
        Args:
            system_prompt: O prompt de sistema para guiar o comportamento da IA
            user_prompt: O prompt do usuário
            options: Parâmetros opcionais de configuração para a geração
            
        Returns:
            str: Uma string vazia, indicando que nenhum texto foi gerado
        """
        self.logger.info("NullTextGenerationService.generate called but no text generation service is available")
        return ""