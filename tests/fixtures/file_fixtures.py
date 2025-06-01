"""
File fixtures for testing.

Este módulo contém fixtures relacionados a arquivos para uso em testes.
"""

import os
import tempfile
import shutil
from typing import Dict, Any, Optional, List, Callable, Generator, Tuple


def temp_directory() -> Generator[str, None, None]:
    """
    Cria um diretório temporário para testes.
    
    Yields:
        str: O caminho para o diretório temporário
        
    Example:
        ```python
        def test_something():
            with temp_directory() as temp_dir:
                # Use temp_dir para testes
                assert os.path.exists(temp_dir)
        ```
    """
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def temp_file(content: str = "", suffix: str = ".txt") -> Generator[str, None, None]:
    """
    Cria um arquivo temporário para testes.
    
    Args:
        content: O conteúdo a ser escrito no arquivo
        suffix: A extensão do arquivo
        
    Yields:
        str: O caminho para o arquivo temporário
        
    Example:
        ```python
        def test_something():
            with temp_file("test content", ".txt") as temp_file_path:
                # Use temp_file_path para testes
                with open(temp_file_path, 'r') as f:
                    assert f.read() == "test content"
        ```
    """
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        yield path
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def mock_video_file(temp_dir: str, filename: str = "test_video.mp4", content: str = "Mock video content") -> str:
    """
    Cria um arquivo de vídeo simulado para testes.
    
    Args:
        temp_dir: O diretório onde o arquivo será criado
        filename: O nome do arquivo
        content: O conteúdo a ser escrito no arquivo
        
    Returns:
        str: O caminho para o arquivo de vídeo simulado
        
    Example:
        ```python
        def test_something():
            with temp_directory() as temp_dir:
                video_file = mock_video_file(temp_dir)
                # Use video_file para testes
                assert os.path.exists(video_file)
        ```
    """
    file_path = os.path.join(temp_dir, filename)
    with open(file_path, 'w') as f:
        f.write(content)
    return file_path


def mock_audio_file(temp_dir: str, filename: str = "test_audio.mp3", content: str = "Mock audio content") -> str:
    """
    Cria um arquivo de áudio simulado para testes.
    
    Args:
        temp_dir: O diretório onde o arquivo será criado
        filename: O nome do arquivo
        content: O conteúdo a ser escrito no arquivo
        
    Returns:
        str: O caminho para o arquivo de áudio simulado
        
    Example:
        ```python
        def test_something():
            with temp_directory() as temp_dir:
                audio_file = mock_audio_file(temp_dir)
                # Use audio_file para testes
                assert os.path.exists(audio_file)
        ```
    """
    file_path = os.path.join(temp_dir, filename)
    with open(file_path, 'w') as f:
        f.write(content)
    return file_path


def create_test_directory_structure(base_dir: str, structure: Dict[str, Any]) -> None:
    """
    Cria uma estrutura de diretórios e arquivos para testes.
    
    Args:
        base_dir: O diretório base onde a estrutura será criada
        structure: Um dicionário descrevendo a estrutura
            - Chaves com valores None ou dict representam diretórios
            - Chaves com valores str representam arquivos, com o valor sendo o conteúdo
            
    Example:
        ```python
        def test_something():
            with temp_directory() as temp_dir:
                structure = {
                    "dir1": {
                        "file1.txt": "content1",
                        "file2.txt": "content2"
                    },
                    "dir2": {
                        "subdir": {}
                    },
                    "file3.txt": "content3"
                }
                create_test_directory_structure(temp_dir, structure)
                # Verifica se a estrutura foi criada
                assert os.path.exists(os.path.join(temp_dir, "dir1", "file1.txt"))
        ```
    """
    for name, content in structure.items():
        path = os.path.join(base_dir, name)
        
        if content is None or isinstance(content, dict):
            # É um diretório
            os.makedirs(path, exist_ok=True)
            if isinstance(content, dict):
                create_test_directory_structure(path, content)
        else:
            # É um arquivo
            with open(path, 'w') as f:
                f.write(str(content))


class TestFileManager:
    """
    Gerenciador de arquivos para testes.
    
    Esta classe facilita a criação e limpeza de arquivos temporários para testes.
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Inicializa o gerenciador de arquivos.
        
        Args:
            base_dir: O diretório base para os arquivos (se None, cria um diretório temporário)
        """
        self.base_dir = base_dir or tempfile.mkdtemp()
        self.created_files = []
        self.created_dirs = []
        self._own_base_dir = base_dir is None
    
    def create_file(self, filename: str, content: str = "") -> str:
        """
        Cria um arquivo para testes.
        
        Args:
            filename: O nome do arquivo (pode incluir subdiretórios)
            content: O conteúdo a ser escrito no arquivo
            
        Returns:
            str: O caminho completo para o arquivo criado
        """
        # Garantir que o diretório pai existe
        dirname = os.path.dirname(filename)
        if dirname:
            full_dirname = os.path.join(self.base_dir, dirname)
            os.makedirs(full_dirname, exist_ok=True)
            if full_dirname not in self.created_dirs:
                self.created_dirs.append(full_dirname)
        
        # Criar o arquivo
        full_path = os.path.join(self.base_dir, filename)
        with open(full_path, 'w') as f:
            f.write(content)
        
        self.created_files.append(full_path)
        return full_path
    
    def create_directory(self, dirname: str) -> str:
        """
        Cria um diretório para testes.
        
        Args:
            dirname: O nome do diretório (pode incluir subdiretórios)
            
        Returns:
            str: O caminho completo para o diretório criado
        """
        full_path = os.path.join(self.base_dir, dirname)
        os.makedirs(full_path, exist_ok=True)
        self.created_dirs.append(full_path)
        return full_path
    
    def cleanup(self) -> None:
        """
        Limpa todos os arquivos e diretórios criados.
        """
        # Remover arquivos
        for file_path in self.created_files:
            try:
                os.unlink(file_path)
            except OSError:
                pass
        
        # Remover diretórios (em ordem reversa para garantir que subdiretórios sejam removidos primeiro)
        for dir_path in reversed(self.created_dirs):
            try:
                os.rmdir(dir_path)
            except OSError:
                pass
        
        # Se criamos o diretório base, removê-lo também
        if self._own_base_dir:
            try:
                shutil.rmtree(self.base_dir, ignore_errors=True)
            except OSError:
                pass
        
        # Limpar as listas
        self.created_files = []
        self.created_dirs = []
    
    def __enter__(self) -> 'TestFileManager':
        """
        Permite o uso com o gerenciador de contexto 'with'.
        
        Returns:
            TestFileManager: A própria instância
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Limpa os arquivos ao sair do contexto 'with'.
        """
        self.cleanup()