"""
Mock objects for MoviePy services.

Este módulo contém implementações de mock para os serviços da MoviePy,
permitindo testes sem dependências externas.
"""

from typing import Dict, Any, Optional, List
from unittest.mock import MagicMock


class MockAudioFileClip:
    """
    Mock para o AudioFileClip da MoviePy.
    
    Esta classe simula o comportamento de um objeto AudioFileClip da MoviePy.
    """
    
    def __init__(self, filename: str, should_fail: bool = False, error_type: Optional[str] = None):
        """
        Inicializa o mock do AudioFileClip.
        
        Args:
            filename: O nome do arquivo de áudio
            should_fail: Indica se as operações devem falhar
            error_type: O tipo de erro a ser simulado
        """
        self.filename = filename
        self.should_fail = should_fail
        self.error_type = error_type
        self.duration = 60.0  # Duração simulada em segundos
        self.fps = 44100
        self.closed = False
    
    def write_audiofile(self, filename: str, bitrate: str = "128k", fps: int = 44100, **kwargs) -> None:
        """
        Simula a escrita de um arquivo de áudio.
        
        Args:
            filename: O nome do arquivo de saída
            bitrate: A taxa de bits para o arquivo de áudio
            fps: A taxa de amostragem para o arquivo de áudio
            **kwargs: Argumentos adicionais
            
        Raises:
            Exception: Se should_fail for True, lança uma exceção do tipo especificado
        """
        if self.should_fail:
            if self.error_type == "permission":
                raise PermissionError(f"Permission denied: {filename}")
            elif self.error_type == "disk_full":
                raise OSError(f"No space left on device: {filename}")
            elif self.error_type == "invalid_format":
                raise ValueError(f"Invalid audio format: {filename}")
            else:
                raise Exception(f"Error writing audio file: {filename}")
        
        # Simular a escrita do arquivo
        with open(filename, 'w') as f:
            f.write(f"Mock audio content for {self.filename} converted to {filename}")
    
    def close(self) -> None:
        """
        Simula o fechamento do clip.
        """
        self.closed = True


class MockMoviePy:
    """
    Mock para o módulo MoviePy.
    
    Esta classe simula o comportamento do módulo MoviePy, fornecendo
    acesso a objetos simulados para testes.
    """
    
    def __init__(self, should_fail: bool = False, error_type: Optional[str] = None):
        """
        Inicializa o mock do módulo MoviePy.
        
        Args:
            should_fail: Indica se as operações devem falhar
            error_type: O tipo de erro a ser simulado
        """
        self.should_fail = should_fail
        self.error_type = error_type
        self.AudioFileClip = self._create_audio_file_clip_class()
    
    def _create_audio_file_clip_class(self):
        """
        Cria uma classe MockAudioFileClip configurada com os parâmetros do mock.
        
        Returns:
            type: Uma classe MockAudioFileClip configurada
        """
        should_fail = self.should_fail
        error_type = self.error_type
        
        class ConfiguredMockAudioFileClip(MockAudioFileClip):
            def __init__(self, filename):
                super().__init__(filename, should_fail=should_fail, error_type=error_type)
        
        return ConfiguredMockAudioFileClip


def create_mock_moviepy(should_fail: bool = False, error_type: Optional[str] = None):
    """
    Cria um mock completo do módulo MoviePy.
    
    Args:
        should_fail: Indica se as operações devem falhar
        error_type: O tipo de erro a ser simulado
        
    Returns:
        MockMoviePy: Um mock do módulo MoviePy
    """
    return MockMoviePy(should_fail=should_fail, error_type=error_type)


def patch_moviepy(should_fail: bool = False, error_type: Optional[str] = None):
    """
    Cria um patch para o módulo MoviePy.
    
    Esta função retorna um dicionário que pode ser usado com patch.dict
    para substituir o módulo MoviePy por um mock.
    
    Args:
        should_fail: Indica se as operações devem falhar
        error_type: O tipo de erro a ser simulado
        
    Returns:
        Dict[str, Any]: Um dicionário para patch.dict
    """
    mock_moviepy = create_mock_moviepy(should_fail=should_fail, error_type=error_type)
    return {"moviepy.AudioFileClip": mock_moviepy.AudioFileClip}