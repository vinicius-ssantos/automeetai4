import os
from typing import Any, Optional, Dict, Callable
from src.interfaces.config_provider import ConfigProvider
from src.config.config_validator import ConfigValidator
from src.utils.logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)


class EnvConfigProvider(ConfigProvider):
    """
    Configuration provider that uses environment variables and in-memory storage.
    Following the Single Responsibility Principle, this class is only responsible
    for providing configuration values.
    """

    def __init__(self, env_prefix: str = "AUTOMEETAI_"):
        """
        Initialize the configuration provider.

        Args:
            env_prefix: Prefix for environment variables
        """
        self.env_prefix = env_prefix
        self._config: Dict[str, Any] = {}
        self._validators: Dict[str, Callable] = {
            # API keys
            "assemblyai_api_key": lambda key: ConfigValidator.validate_api_key(key, "AssemblyAI"),
            "openai_api_key": lambda key: ConfigValidator.validate_api_key(key, "OpenAI"),

            # Rate limits
            "assemblyai_rate_limit": lambda rate: ConfigValidator.validate_rate_limit(rate, "AssemblyAI"),
            "openai_rate_limit": lambda rate: ConfigValidator.validate_rate_limit(rate, "OpenAI"),

            # Transcription settings
            "language_code": ConfigValidator.validate_language_code,
            "speakers_expected": ConfigValidator.validate_speakers_expected,

            # Model names
            "openai_model": lambda model: ConfigValidator.validate_model_name(model, ["gpt-3.5-turbo", "gpt-4", "gpt-4o", "gpt-4o-2024-08-06"]),

            # Directories
            "output_directory": lambda dir: ConfigValidator.validate_directory(dir, create_if_missing=True)
        }

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get a configuration value by key.
        First checks in-memory storage, then environment variables.

        Args:
            key: The configuration key
            default: Default value to return if the key is not found

        Returns:
            Any: The configuration value
        """
        # Check in-memory storage first
        if key in self._config:
            value = self._config[key]
        else:
            # Then check environment variables
            env_key = f"{self.env_prefix}{key.upper()}"
            env_value = os.environ.get(env_key)
            if env_value is not None:
                value = env_value
            else:
                # Return default if not found
                return default

        # Validate the value if a validator exists for this key
        if key in self._validators:
            try:
                return self._validators[key](value)
            except ValueError as e:
                logger.warning(f"Invalid configuration value for {key}: {e}")
                # Return the original value if validation fails
                return value

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value in in-memory storage.

        Args:
            key: The configuration key
            value: The configuration value
        """
        self._config[key] = value
