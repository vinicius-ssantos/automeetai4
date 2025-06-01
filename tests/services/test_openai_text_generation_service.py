import unittest
from unittest.mock import Mock, patch, MagicMock
import os

from src.services.openai_text_generation_service import OpenAITextGenerationService, USING_OPENAI_V1
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

        # Setup mocks based on OpenAI version
        if USING_OPENAI_V1:
            # For OpenAI v1.0.0+
            patcher_openai = patch('src.services.openai_text_generation_service.OpenAI')
            self.mock_openai_class = patcher_openai.start()
            self.addCleanup(patcher_openai.stop)

            # Criar um mock para o cliente OpenAI
            self.mock_openai_client = MagicMock()
            self.mock_openai_class.return_value = self.mock_openai_client

            # Configurar o mock do cliente OpenAI
            self.mock_chat_completions = MagicMock()
            self.mock_openai_client.chat.completions = self.mock_chat_completions
        else:
            # For older versions of OpenAI
            patcher_openai = patch('src.services.openai_text_generation_service.openai')
            self.mock_openai_module = patcher_openai.start()
            self.addCleanup(patcher_openai.stop)

            # Configurar o mock do módulo OpenAI
            self.mock_chat_completion = MagicMock()
            self.mock_openai_module.ChatCompletion = self.mock_chat_completion

        # Criar o serviço com o mock do ConfigProvider
        self.service = OpenAITextGenerationService(self.config_provider)

    @patch('src.services.openai_text_generation_service.RateLimiterRegistry')
    def test_generate_success(self, mock_rate_limiter_registry):
        """Testa a geração de texto bem-sucedida."""
        # Configurar mocks
        mock_rate_limiter = Mock()
        mock_rate_limiter_registry.return_value.get_limiter.return_value = mock_rate_limiter

        if USING_OPENAI_V1:
            # For OpenAI v1.0.0+
            # Configurar resposta do OpenAI
            mock_choice = MagicMock()
            mock_choice.message.content = "Generated text response"

            mock_response = MagicMock()
            mock_response.choices = [mock_choice]

            self.mock_chat_completions.create.return_value = mock_response
        else:
            # For older versions of OpenAI
            mock_response = {
                'choices': [
                    {
                        'message': {
                            'content': "Generated text response"
                        }
                    }
                ]
            }
            self.mock_chat_completion.create.return_value = mock_response

        # Chamar o método generate
        result = self.service.generate(
            system_prompt="System prompt for testing",
            user_prompt="User prompt for testing"
        )

        # Verificar se o resultado é o esperado
        self.assertEqual(result, "Generated text response")

        # Verificar se os métodos foram chamados corretamente
        mock_rate_limiter.consume.assert_called_once_with(wait=True)

        expected_args = {
            'model': "gpt-3.5-turbo",
            'messages': [
                {"role": "system", "content": "System prompt for testing"},
                {"role": "user", "content": "User prompt for testing"}
            ],
            'temperature': 0.7
        }

        if USING_OPENAI_V1:
            self.mock_chat_completions.create.assert_called_once_with(**expected_args)
        else:
            self.mock_chat_completion.create.assert_called_once_with(**expected_args)

    @patch('src.services.openai_text_generation_service.RateLimiterRegistry')
    def test_generate_with_custom_options(self, mock_rate_limiter_registry):
        """Testa a geração de texto com opções personalizadas."""
        # Configurar mocks
        mock_rate_limiter = Mock()
        mock_rate_limiter_registry.return_value.get_limiter.return_value = mock_rate_limiter

        if USING_OPENAI_V1:
            # For OpenAI v1.0.0+
            # Configurar resposta do OpenAI
            mock_choice = MagicMock()
            mock_choice.message.content = "Generated text response"

            mock_response = MagicMock()
            mock_response.choices = [mock_choice]

            self.mock_chat_completions.create.return_value = mock_response
        else:
            # For older versions of OpenAI
            mock_response = {
                'choices': [
                    {
                        'message': {
                            'content': "Generated text response"
                        }
                    }
                ]
            }
            self.mock_chat_completion.create.return_value = mock_response

        # Chamar o método generate com opções personalizadas
        result = self.service.generate(
            system_prompt="System prompt for testing",
            user_prompt="User prompt for testing",
            options={"temperature": 0.3}
        )

        # Verificar se o resultado é o esperado
        self.assertEqual(result, "Generated text response")

        # Verificar se os métodos foram chamados com as opções personalizadas
        expected_args = {
            'model': "gpt-3.5-turbo",
            'messages': [
                {"role": "system", "content": "System prompt for testing"},
                {"role": "user", "content": "User prompt for testing"}
            ],
            'temperature': 0.3
        }

        if USING_OPENAI_V1:
            self.mock_chat_completions.create.assert_called_once_with(**expected_args)
        else:
            self.mock_chat_completion.create.assert_called_once_with(**expected_args)

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
        if USING_OPENAI_V1:
            self.mock_chat_completions.create.side_effect = ValueError("Invalid input")
        else:
            self.mock_chat_completion.create.side_effect = ValueError("Invalid input")

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
        if USING_OPENAI_V1:
            self.mock_chat_completions.create.side_effect = ConnectionError("Network error")
        else:
            self.mock_chat_completion.create.side_effect = ConnectionError("Network error")

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
        if USING_OPENAI_V1:
            self.mock_chat_completions.create.side_effect = TimeoutError("Request timed out")
        else:
            self.mock_chat_completion.create.side_effect = TimeoutError("Request timed out")

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
        if USING_OPENAI_V1:
            self.mock_chat_completions.create.side_effect = Exception("General error")
        else:
            self.mock_chat_completion.create.side_effect = Exception("General error")

        # Chamar o método generate
        result = self.service.generate(
            system_prompt="System prompt for testing",
            user_prompt="User prompt for testing"
        )

        # Verificar se o resultado é uma string vazia (falha)
        self.assertEqual(result, "")


if __name__ == '__main__':
    unittest.main()
