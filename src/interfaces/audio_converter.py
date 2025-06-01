from abc import ABC, abstractmethod
from typing import Optional, List

from src.exceptions import FileError, ServiceError


class AudioConverter(ABC):
    """
    Interface for audio conversion services.
    Following the Interface Segregation Principle, this interface defines
    only the methods needed for audio conversion.
    """

    @abstractmethod
    def convert(self, input_file: str, output_file: str, 
              allowed_input_extensions: Optional[List[str]] = None,
              allowed_output_extensions: Optional[List[str]] = None) -> bool:
        """
        Convert an audio file from one format to another.

        Args:
            input_file: Path to the input audio file
            output_file: Path where the converted file will be saved
            allowed_input_extensions: Optional list of allowed input file extensions
            allowed_output_extensions: Optional list of allowed output file extensions

        Returns:
            bool: True if conversion was successful, False otherwise
        """
        pass
