import unittest
from unittest.mock import patch
from src.services.null_text_generation_service import NullTextGenerationService


class TestNullTextGenerationService(unittest.TestCase):
    """
    Testes para o NullTextGenerationService.

    Esta classe de teste verifica se o NullTextGenerationService implementa
    corretamente o padrão Null Object, retornando valores neutros e não
    causando erros quando seus métodos são chamados.
    """

    def setUp(self):
        """Configuração para cada teste."""
        self.service = NullTextGenerationService()

    def test_initialization(self):
        """Testa se o serviço é inicializado corretamente."""
        self.assertIsInstance(self.service, NullTextGenerationService)

    def test_generate_returns_empty_string(self):
        """Testa se o método generate retorna uma string vazia."""
        # Patch the logger directly on the instance
        original_logger = self.service.logger
        try:
            # Replace the logger with a mock
            mock_logger = unittest.mock.Mock()
            self.service.logger = mock_logger

            # Chamar o método generate
            result = self.service.generate(
                system_prompt="System prompt for testing",
                user_prompt="User prompt for testing",
                options={"temperature": 0.5}
            )

            # Verificar se uma string vazia foi retornada
            self.assertEqual(result, "")

            # Verificar se o logger foi chamado
            mock_logger.info.assert_called_once_with("NullTextGenerationService.generate called but no text generation service is available")
        finally:
            # Restore the original logger
            self.service.logger = original_logger

    def test_generate_with_different_parameters(self):
        """Testa se o método generate funciona com diferentes parâmetros."""
        # Teste com parâmetros vazios
        result1 = self.service.generate("", "", None)
        self.assertEqual(result1, "")

        # Teste com parâmetros longos
        long_text = "A" * 1000
        result2 = self.service.generate(long_text, long_text, {"complex": "option"})
        self.assertEqual(result2, "")


if __name__ == '__main__':
    unittest.main()
