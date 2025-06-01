from abc import ABC, abstractmethod
from typing import Any, Optional


class ConfigProvider(ABC):
    """
    Interface for configuration providers.
    Following the Dependency Inversion Principle, high-level modules should depend on abstractions,
    not concrete implementations of configuration providers.
    """
    
    @abstractmethod
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: The configuration key
            default: Default value to return if the key is not found
            
        Returns:
            Any: The configuration value
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: The configuration key
            value: The configuration value
        """
        pass