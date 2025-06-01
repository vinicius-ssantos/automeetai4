from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class TextGenerationService(ABC):
    """
    Interface for AI text generation services.
    Following the Interface Segregation Principle, this interface defines
    only the methods needed for text generation.
    """

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate text using an AI model.

        Args:
            system_prompt: The system prompt to guide the AI's behavior
            user_prompt: The user's input prompt
            options: Optional configuration parameters for the generation

        Returns:
            str: The generated text, or an empty string if generation failed
        """
        pass
