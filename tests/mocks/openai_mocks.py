"""
Mock objects for OpenAI services.

Este módulo contém implementações de mock para os serviços da OpenAI,
permitindo testes sem dependências externas.
"""

from typing import Dict, Any, Optional, List
from unittest.mock import MagicMock


class MockOpenAIMessage:
    """
    Mock para uma mensagem da OpenAI.
    
    Esta classe simula o comportamento de um objeto de mensagem retornado
    pela API da OpenAI.
    """
    
    def __init__(self, content: str, role: str = "assistant"):
        """
        Inicializa o mock de mensagem.
        
        Args:
            content: O conteúdo da mensagem
            role: O papel do emissor da mensagem (system, user, assistant)
        """
        self.content = content
        self.role = role


class MockOpenAIChoice:
    """
    Mock para uma escolha da OpenAI.
    
    Esta classe simula o comportamento de um objeto de escolha retornado
    pela API da OpenAI.
    """
    
    def __init__(self, message_content: str, role: str = "assistant", index: int = 0):
        """
        Inicializa o mock de escolha.
        
        Args:
            message_content: O conteúdo da mensagem
            role: O papel do emissor da mensagem
            index: O índice da escolha
        """
        self.index = index
        self.message = MockOpenAIMessage(content=message_content, role=role)
        self.finish_reason = "stop"


class MockOpenAIResponse:
    """
    Mock para uma resposta da OpenAI.
    
    Esta classe simula o comportamento de um objeto de resposta retornado
    pela API da OpenAI.
    """
    
    def __init__(self, message_content: str = "Mock response from OpenAI"):
        """
        Inicializa o mock de resposta.
        
        Args:
            message_content: O conteúdo da mensagem na resposta
        """
        self.id = "mock-response-id-12345"
        self.object = "chat.completion"
        self.created = 1677858242
        self.model = "gpt-3.5-turbo"
        self.choices = [MockOpenAIChoice(message_content=message_content)]
        self.usage = {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }


class MockOpenAIChatCompletions:
    """
    Mock para o serviço de chat completions da OpenAI.
    
    Esta classe simula o comportamento do serviço de chat completions da OpenAI.
    """
    
    def __init__(self, should_fail: bool = False, error_type: Optional[str] = None):
        """
        Inicializa o mock do serviço de chat completions.
        
        Args:
            should_fail: Indica se a geração deve falhar
            error_type: O tipo de erro a ser simulado
        """
        self.should_fail = should_fail
        self.error_type = error_type
        self.responses = {}
    
    def create(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.7) -> MockOpenAIResponse:
        """
        Simula a criação de uma completação de chat.
        
        Args:
            model: O modelo a ser usado
            messages: As mensagens para o chat
            temperature: A temperatura para a geração
            
        Returns:
            MockOpenAIResponse: Uma resposta simulada
            
        Raises:
            Exception: Se should_fail for True, lança uma exceção do tipo especificado
        """
        if self.should_fail:
            if self.error_type == "auth":
                raise ValueError("Invalid API key")
            elif self.error_type == "rate_limit":
                raise ConnectionError("Rate limit exceeded")
            elif self.error_type == "timeout":
                raise TimeoutError("Request timed out")
            else:
                raise Exception("Generic OpenAI error")
        
        # Gerar uma resposta com base nas mensagens
        system_prompt = ""
        user_prompt = ""
        
        for message in messages:
            if message["role"] == "system":
                system_prompt = message["content"]
            elif message["role"] == "user":
                user_prompt = message["content"]
        
        # Criar uma resposta simulada
        response_text = f"Response to: {user_prompt[:30]}..."
        response = MockOpenAIResponse(message_content=response_text)
        
        # Armazenar a resposta para referência futura
        key = f"{model}_{temperature}_{hash(str(messages))}"
        self.responses[key] = response
        
        return response


class MockOpenAIClient:
    """
    Mock para o cliente da OpenAI.
    
    Esta classe simula o comportamento do cliente da OpenAI.
    """
    
    def __init__(self, api_key: Optional[str] = None, should_fail: bool = False, error_type: Optional[str] = None):
        """
        Inicializa o mock do cliente.
        
        Args:
            api_key: A chave de API
            should_fail: Indica se as operações devem falhar
            error_type: O tipo de erro a ser simulado
        """
        self.api_key = api_key
        self.should_fail = should_fail
        self.error_type = error_type
        self.chat = MagicMock()
        self.chat.completions = MockOpenAIChatCompletions(should_fail=should_fail, error_type=error_type)


class MockOpenAI:
    """
    Mock para o módulo OpenAI.
    
    Esta classe simula o comportamento do módulo OpenAI, fornecendo
    acesso a objetos simulados para testes.
    """
    
    def __init__(self, api_key: Optional[str] = None, should_fail: bool = False, error_type: Optional[str] = None):
        """
        Inicializa o mock do módulo OpenAI.
        
        Args:
            api_key: A chave de API
            should_fail: Indica se as operações devem falhar
            error_type: O tipo de erro a ser simulado
        """
        self.api_key = api_key
        self.should_fail = should_fail
        self.error_type = error_type
    
    def __call__(self, api_key: Optional[str] = None):
        """
        Cria um novo cliente simulado.
        
        Args:
            api_key: A chave de API
            
        Returns:
            MockOpenAIClient: Um cliente simulado
        """
        return MockOpenAIClient(api_key=api_key or self.api_key, should_fail=self.should_fail, error_type=self.error_type)


def create_mock_openai(should_fail: bool = False, error_type: Optional[str] = None):
    """
    Cria um mock completo do módulo OpenAI.
    
    Args:
        should_fail: Indica se as operações devem falhar
        error_type: O tipo de erro a ser simulado
        
    Returns:
        MockOpenAI: Um mock do módulo OpenAI
    """
    return MockOpenAI(api_key="mock-api-key", should_fail=should_fail, error_type=error_type)