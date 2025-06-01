import os
import pytest
from src.services.openai_text_generation_service import OpenAITextGenerationService
from src.interfaces.config_provider import ConfigProvider

class TestConfigProvider(ConfigProvider):
    """A simple config provider for testing that reads from environment variables."""
    
    def get(self, key, default=None):
        """Get a configuration value."""
        import os
        return os.environ.get(key, default)


@pytest.mark.manual
class TestOpenAITextGenerationServiceReal:
    """
    Tests for the OpenAITextGenerationService using the real API.
    
    These tests call the real OpenAI API and consume credits.
    They are marked with @pytest.mark.manual and will be skipped by default.
    To run these tests, use: pytest tests/test_openai_text_generation_service_real.py --manual
    """
    
    def setup_method(self):
        """Set up the test environment."""
        # Use a config provider that reads from environment variables
        self.config_provider = TestConfigProvider()
        
        # Create the service
        self.service = OpenAITextGenerationService(self.config_provider)
    
    def test_generate_real_text(self):
        """Test generating text using the OpenAI API."""
        # Skip if no API key is set
        api_key = os.environ.get("AUTOMEETAI_OPENAI_API_KEY")
        if not api_key:
            pytest.skip("AUTOMEETAI_OPENAI_API_KEY environment variable not set")
        
        # Define system and user prompts
        system_prompt = "You are a helpful assistant that provides concise answers."
        user_prompt = "What is the capital of France?"
        
        # Generate text
        result = self.service.generate(system_prompt, user_prompt)
        
        # Verify the result
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Print the generated text for manual verification
        print(f"\nGenerated text:")
        print(f"{result}")
    
    def test_generate_with_custom_options(self):
        """Test generating text with custom options using the OpenAI API."""
        # Skip if no API key is set
        api_key = os.environ.get("AUTOMEETAI_OPENAI_API_KEY")
        if not api_key:
            pytest.skip("AUTOMEETAI_OPENAI_API_KEY environment variable not set")
        
        # Define system and user prompts
        system_prompt = "You are a helpful assistant that provides creative answers."
        user_prompt = "Write a short poem about programming."
        
        # Define custom options
        options = {
            "temperature": 0.9  # Higher temperature for more creative output
        }
        
        # Generate text
        result = self.service.generate(system_prompt, user_prompt, options)
        
        # Verify the result
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Print the generated text for manual verification
        print(f"\nGenerated text with custom options:")
        print(f"{result}")