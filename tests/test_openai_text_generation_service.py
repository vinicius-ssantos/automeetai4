import unittest
from unittest.mock import Mock, patch, MagicMock
import os

from src.services.openai_text_generation_service import OpenAITextGenerationService
from src.interfaces.config_provider import ConfigProvider


class TestOpenAITextGenerationService(unittest.TestCase):
    """
    Testes para o OpenAITextGenerationService.

    Esta classe de teste verifica se o OpenAITextGenerationService gera
    texto corretamente usando a API da OpenAI.
    """

    def setUp(self):
        """Configuração para cada teste."""
        # Criar um mock para o ConfigProvider
        self.config_provider = Mock(spec=ConfigProvider)

        # Configurar valores padrão para o mock
        self.config_provider.get.side_effect = lambda key, default: {
            "openai_api_key": "test_api_key_12345678901234567890",
            "openai_model": "gpt-3.5-turbo"
        }.get(key, default)

        # Patch para o validate_api_key para evitar erros de validação
        patcher = patch.object(OpenAITextGenerationService, '_validate_api_key')
        self.mock_validate_api_key = patcher.start()
        self.addCleanup(patcher.stop)

        # Patch para o OpenAI client
        patcher_openai = patch('src.services.openai_text_generation_service.OpenAI')
        self.mock_openai = patcher_openai.start()
        self.addCleanup(patcher_openai.stop)

        # Configurar o mock do cliente OpenAI
        self.mock_client = Mock()
        self.mock_openai.return_value = self.mock_client

        # Criar o serviço com o mock do ConfigProvider
        self.service = OpenAITextGenerationService(self.config_provider)

    @patch('src.services.openai_text_generation_service.RateLimiterRegistry')
    def test_generate_success(self, mock_rate_limiter_registry):
        """Testa a geração de texto bem-sucedida."""
        # Configurar mocks
        mock_rate_limiter = Mock()
        mock_rate_limiter_registry.return_value.get_limiter.return_value = mock_rate_limiter

        # Configurar resposta do OpenAI
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "Generated text response"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        self.mock_client.chat.completions.create.return_value = mock_response

        # Chamar o método generate
        result = self.service.generate(
            system_prompt="System prompt for testing",
            user_prompt="User prompt for testing"
        )

        # Verificar se o resultado é o esperado
        self.assertEqual(result, "Generated text response")

        # Verificar se os métodos foram chamados corretamente
        mock_rate_limiter.consume.assert_called_once_with(wait=True)
        self.mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "System prompt for testing"},
                {"role": "user", "content": "User prompt for testing"}
            ],
            temperature=0.7
        )

    @patch('src.services.openai_text_generation_service.RateLimiterRegistry')
    def test_generate_with_custom_options(self, mock_rate_limiter_registry):
        """Testa a geração de texto com opções personalizadas."""
        # Configurar mocks
        mock_rate_limiter = Mock()
        mock_rate_limiter_registry.return_value.get_limiter.return_value = mock_rate_limiter

        # Configurar resposta do OpenAI
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "Generated text response"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        self.mock_client.chat.completions.create.return_value = mock_response

        # Chamar o método generate com opções personalizadas
        result = self.service.generate(
            system_prompt="System prompt for testing",
            user_prompt="User prompt for testing",
            options={"temperature": 0.3}
        )

        # Verificar se o resultado é o esperado
        self.assertEqual(result, "Generated text response")

        # Verificar se os métodos foram chamados com as opções personalizadas
        self.mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "System prompt for testing"},
                {"role": "user", "content": "User prompt for testing"}
            ],
            temperature=0.3
        )

    def test_generate_client_not_initialized(self):
        """Testa o comportamento quando o cliente OpenAI não está inicializado."""
        # Usar o serviço já criado no setUp, mas forçar o cliente a ser None
        self.service.client = None

        # Chamar o método generate
        result = self.service.generate(
            system_prompt="System prompt for testing",
            user_prompt="User prompt for testing"
        )

        # Verificar se o resultado é uma string vazia (falha)
        self.assertEqual(result, "")

    @patch('src.services.openai_text_generation_service.RateLimiterRegistry')
    def test_generate_value_error(self, mock_rate_limiter_registry):
        """Testa o comportamento quando ocorre um erro de valor."""
        # Configurar mocks
        mock_rate_limiter = Mock()
        mock_rate_limiter_registry.return_value.get_limiter.return_value = mock_rate_limiter

        # Configurar o cliente para lançar ValueError
        self.mock_client.chat.completions.create.side_effect = ValueError("Invalid input")

        # Chamar o método generate
        result = self.service.generate(
            system_prompt="System prompt for testing",
            user_prompt="User prompt for testing"
        )

        # Verificar se o resultado é uma string vazia (falha)
        self.assertEqual(result, "")

    @patch('src.services.openai_text_generation_service.RateLimiterRegistry')
    def test_generate_connection_error(self, mock_rate_limiter_registry):
        """Testa o comportamento quando ocorre um erro de conexão."""
        # Configurar mocks
        mock_rate_limiter = Mock()
        mock_rate_limiter_registry.return_value.get_limiter.return_value = mock_rate_limiter

        # Configurar o cliente para lançar ConnectionError
        self.mock_client.chat.completions.create.side_effect = ConnectionError("Network error")

        # Chamar o método generate
        result = self.service.generate(
            system_prompt="System prompt for testing",
            user_prompt="User prompt for testing"
        )

        # Verificar se o resultado é uma string vazia (falha)
        self.assertEqual(result, "")

    @patch('src.services.openai_text_generation_service.RateLimiterRegistry')
    def test_generate_timeout_error(self, mock_rate_limiter_registry):
        """Testa o comportamento quando ocorre um erro de timeout."""
        # Configurar mocks
        mock_rate_limiter = Mock()
        mock_rate_limiter_registry.return_value.get_limiter.return_value = mock_rate_limiter

        # Configurar o cliente para lançar TimeoutError
        self.mock_client.chat.completions.create.side_effect = TimeoutError("Request timed out")

        # Chamar o método generate
        result = self.service.generate(
            system_prompt="System prompt for testing",
            user_prompt="User prompt for testing"
        )

        # Verificar se o resultado é uma string vazia (falha)
        self.assertEqual(result, "")

    @patch('src.services.openai_text_generation_service.RateLimiterRegistry')
    def test_generate_general_exception(self, mock_rate_limiter_registry):
        """Testa o comportamento quando ocorre uma exceção genérica."""
        # Configurar mocks
        mock_rate_limiter = Mock()
        mock_rate_limiter_registry.return_value.get_limiter.return_value = mock_rate_limiter

        # Configurar o cliente para lançar Exception
        self.mock_client.chat.completions.create.side_effect = Exception("General error")

        # Chamar o método generate
        result = self.service.generate(
            system_prompt="System prompt for testing",
            user_prompt="User prompt for testing"
        )

        # Verificar se o resultado é uma string vazia (falha)
        self.assertEqual(result, "")


if __name__ == '__main__':
    unittest.main()
