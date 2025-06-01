from typing import Optional
from src.automeetai import AutoMeetAI
from abc import ABC, abstractmethod

class AutoMeetAIFactoryInterface(ABC):
    """
    Interface para fábricas de AutoMeetAI.
    Define os métodos que todas as implementações de fábrica devem ter.
    """
    
    @abstractmethod
    def create(
        self,
        assemblyai_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        include_text_generation: bool = True
    ) -> AutoMeetAI:
        """
        Cria uma nova instância de AutoMeetAI com todas as dependências necessárias.
        
        Args:
            assemblyai_api_key: Chave de API para AssemblyAI
            openai_api_key: Chave de API para OpenAI
            include_text_generation: Se deve incluir o serviço de geração de texto
            
        Returns:
            AutoMeetAI: Uma instância configurada de AutoMeetAI
        """
        pass