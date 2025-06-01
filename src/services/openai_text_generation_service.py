from typing import Optional, Dict, Any
import openai
from src.interfaces.text_generation_service import TextGenerationService
from src.interfaces.config_provider import ConfigProvider
from src.utils.rate_limiter import RateLimiterRegistry
from src.utils.logging import get_logger
from src.config.default_config import (
    OPENAI_API_KEY, 
    OPENAI_MODEL,
    OPENAI_RATE_LIMIT,
    OPENAI_RATE_LIMIT_PER,
    OPENAI_RATE_LIMIT_BURST
)

# Check if we're using OpenAI v1.0.0+ or an older version
try:
    from openai import OpenAI
    USING_OPENAI_V1 = True
except ImportError:
    USING_OPENAI_V1 = False


class OpenAITextGenerationService(TextGenerationService):
    """
    Implementation of TextGenerationService using OpenAI.
    Following the Single Responsibility Principle, this class is only responsible
    for generating text using OpenAI.
    """

    # Initialize logger for this class
    logger = get_logger(__name__)

    def __init__(self, config_provider: Optional[ConfigProvider] = None):
        """
        Initialize the text generation service.

        Args:
            config_provider: Optional configuration provider
        """
        self.config_provider = config_provider

        # Get API key from config provider or default
        api_key = None
        if self.config_provider:
            api_key = self.config_provider.get("openai_api_key", OPENAI_API_KEY)
        else:
            api_key = OPENAI_API_KEY

        # Validate API key
        self._validate_api_key(api_key)

        # Initialize OpenAI client based on version
        if api_key:
            if USING_OPENAI_V1:
                # For OpenAI v1.0.0+
                self.client = OpenAI(api_key=api_key)
            else:
                # For older versions of OpenAI
                openai.api_key = api_key
                self.client = openai
        else:
            self.client = None

        # Get model from config provider or default
        self.model = None
        if self.config_provider:
            self.model = self.config_provider.get("openai_model", OPENAI_MODEL)
        else:
            self.model = OPENAI_MODEL

    def _validate_api_key(self, api_key: Optional[str]) -> None:
        """
        Validate the API key.

        Args:
            api_key: The API key to validate

        Raises:
            ValueError: If the API key is invalid
        """
        if not api_key:
            self.logger.warning("OpenAI API key is not provided. Service will be initialized but text generation will not work.")
            return

        if not isinstance(api_key, str):
            raise ValueError("OpenAI API key must be a string.")

        if len(api_key.strip()) < 20:  # Basic validation for key length
            raise ValueError("OpenAI API key appears to be invalid. Please check your API key.")

    def generate(self, system_prompt: str, user_prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate text using OpenAI.

        Args:
            system_prompt: The system prompt to guide the AI's behavior
            user_prompt: The user's input prompt
            options: Optional configuration parameters for the generation

        Returns:
            str: The generated text, or an empty string if generation failed
        """
        try:
            if not self.client:
                error_msg = "OpenAI client is not initialized. Please provide a valid API key."
                self.logger.error(error_msg)
                return ""

            # Set default options
            generation_options = {
                "temperature": 0.7
            }

            # Override with provided options if any
            if options:
                generation_options.update(options)

            # Get rate limiter for OpenAI
            rate_limiter = RateLimiterRegistry().get_limiter(
                "openai",
                rate=OPENAI_RATE_LIMIT,
                per=OPENAI_RATE_LIMIT_PER,
                burst=OPENAI_RATE_LIMIT_BURST
            )

            # Wait for a token to become available (rate limiting)
            rate_limiter.consume(wait=True)

            # Generate response based on OpenAI version
            if USING_OPENAI_V1:
                # For OpenAI v1.0.0+
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=generation_options["temperature"]
                )
                # Extract and return the generated text
                generated_text = response.choices[0].message.content.strip()
            else:
                # For older versions of OpenAI
                response = self.client.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=generation_options["temperature"]
                )
                # Extract and return the generated text
                generated_text = response['choices'][0]['message']['content'].strip()
            return generated_text

        except ValueError as e:
            error_msg = f"Invalid input or configuration: {e}"
            self.logger.error(error_msg)
            return ""

        except ImportError as e:
            error_msg = f"OpenAI library not properly installed: {e}"
            self.logger.error(error_msg)
            return ""

        except ConnectionError as e:
            error_msg = f"Network error during OpenAI API call: {e}"
            self.logger.error(error_msg)
            return ""

        except TimeoutError as e:
            error_msg = f"Timeout during OpenAI API call: {e}"
            self.logger.error(error_msg)
            return ""

        except Exception as e:
            error_msg = f"An error occurred during text generation: {e}"
            self.logger.error(error_msg)
            return ""
