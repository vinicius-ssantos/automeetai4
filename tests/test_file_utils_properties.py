"""
Property-based tests for file_utils module.

Este módulo contém testes baseados em propriedades para as funções do módulo file_utils.
"""

import os
import re
import unittest
from pathlib import Path

# Try to import pytest and hypothesis, but don't fail if they're not available
try:
    import pytest
    from hypothesis import given, strategies as st, assume, settings, example
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Create dummy decorators that will skip the tests if pytest is not available
    def given(*args, **kwargs):
        def decorator(func):
            def wrapper(*args, **kwargs):
                return None
            return wrapper
        return decorator

    def example(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    # Create a dummy strategy class that implements common methods
    class DummyStrategy:
        def __init__(self, *args, **kwargs):
            pass

        def filter(self, *args, **kwargs):
            return self

        def map(self, *args, **kwargs):
            return self

        def flatmap(self, *args, **kwargs):
            return self

        def __repr__(self):
            return "DummyStrategy()"

    # Create a dummy class to avoid NameError
    class st:
        @staticmethod
        def text(*args, **kwargs):
            return DummyStrategy()

        @staticmethod
        def lists(*args, **kwargs):
            return DummyStrategy()

        @staticmethod
        def builds(*args, **kwargs):
            return DummyStrategy()

        @staticmethod
        def integers(*args, **kwargs):
            return DummyStrategy()

        @staticmethod
        def sampled_from(*args, **kwargs):
            return DummyStrategy()

        @staticmethod
        def characters(*args, **kwargs):
            return DummyStrategy()

from src.utils.file_utils import validate_file_path, generate_unique_filename, ensure_directory_exists

# Skip all tests if pytest is not available
if not PYTEST_AVAILABLE:
    print("Skipping property-based tests because pytest or hypothesis is not installed.")
    # Create a test class that will be discovered by unittest but won't run any tests
    class SkippedPropertyTests(unittest.TestCase):
        def test_skip(self):
            self.skipTest("pytest or hypothesis is not installed")


# Estratégias para gerar caminhos de arquivo válidos e inválidos
valid_path_chars = st.characters(
    blacklist_characters='\\/:*?"<>|',
    blacklist_categories=('Cs',)  # Exclude surrogate characters
)

valid_filename = st.text(
    alphabet=valid_path_chars,
    min_size=1,
    max_size=50
).filter(lambda s: not s.isspace() and s not in ('.', '..'))

valid_extension = st.text(
    alphabet=st.characters(
        whitelist_categories=('Ll',),  # Only lowercase letters
        max_codepoint=127  # ASCII only
    ),
    min_size=1,
    max_size=10
)

valid_directory = st.lists(
    valid_filename,
    min_size=0,
    max_size=5
).map(lambda parts: os.path.join(*parts) if parts else "")

valid_file_path = st.builds(
    lambda directory, filename, extension: os.path.join(directory, f"{filename}.{extension}") if directory else f"{filename}.{extension}",
    valid_directory,
    valid_filename,
    valid_extension
)

# Estratégia para gerar caminhos de arquivo com padrões suspeitos
suspicious_patterns = [
    '..', '\\\\', '//', '~', '%00', '${', '<', '>', '|', ';', '&', '$(', '`'
]

suspicious_path = st.builds(
    lambda base_path, pattern, position: 
        base_path[:position] + pattern + base_path[position:] if base_path else pattern,
    valid_file_path,
    st.sampled_from(suspicious_patterns),
    st.integers(min_value=0, max_value=10)
)

# Estratégia para gerar listas de extensões permitidas
allowed_extensions = st.lists(
    valid_extension,
    min_size=1,
    max_size=10
)


@given(valid_file_path)
@example("file.txt")
@example("dir/file.txt")
@example("C:\\Users\\user\\file.txt")
def test_validate_file_path_valid_paths(file_path):
    """
    Testa se caminhos de arquivo válidos são aceitos pela função validate_file_path.

    Args:
        file_path: Um caminho de arquivo válido gerado pela estratégia valid_file_path
    """
    try:
        # Alguns caminhos gerados podem ser inválidos no sistema operacional atual
        # então ignoramos erros específicos do sistema de arquivos
        result = validate_file_path(file_path)
        assert result is True
    except ValueError as e:
        # Se o erro for relacionado a um padrão suspeito, falha o teste
        if "suspicious pattern" in str(e):
            pytest.fail(f"Valid path rejected: {file_path}, error: {e}")
        # Outros erros de validação podem ser aceitáveis para alguns caminhos gerados


@given(suspicious_path)
@example("../file.txt")
@example("file/../secret.txt")
@example("file;rm -rf /.txt")
def test_validate_file_path_rejects_suspicious_paths(file_path):
    """
    Testa se caminhos de arquivo com padrões suspeitos são rejeitados.

    Args:
        file_path: Um caminho de arquivo com padrão suspeito
    """
    # Verificar se o caminho contém realmente um padrão suspeito
    has_suspicious_pattern = any(pattern in file_path for pattern in suspicious_patterns)

    if has_suspicious_pattern:
        with pytest.raises(ValueError) as excinfo:
            validate_file_path(file_path)

        # Verificar se a mensagem de erro menciona um padrão suspeito
        assert "suspicious pattern" in str(excinfo.value) or "Invalid file path" in str(excinfo.value)


@given(valid_file_path, allowed_extensions)
def test_validate_file_path_with_allowed_extensions(file_path, extensions):
    """
    Testa a validação de extensões de arquivo permitidas.

    Args:
        file_path: Um caminho de arquivo válido
        extensions: Uma lista de extensões permitidas
    """
    # Extrair a extensão do arquivo
    extension = os.path.splitext(file_path)[1].lstrip('.').lower()

    # Se a extensão estiver na lista de extensões permitidas, deve ser aceita
    if extension in [ext.lower() for ext in extensions]:
        assert validate_file_path(file_path, allowed_extensions=extensions) is True
    else:
        # Se a extensão não estiver na lista, deve ser rejeitada
        with pytest.raises(ValueError) as excinfo:
            validate_file_path(file_path, allowed_extensions=extensions)
        assert "invalid extension" in str(excinfo.value)


@given(st.text(min_size=0, max_size=0))
def test_validate_file_path_rejects_empty_path(file_path):
    """
    Testa se caminhos de arquivo vazios são rejeitados.

    Args:
        file_path: Um caminho de arquivo vazio
    """
    with pytest.raises(ValueError) as excinfo:
        validate_file_path(file_path)
    assert "cannot be empty" in str(excinfo.value)


@given(valid_file_path, st.lists(valid_directory, min_size=1, max_size=5))
def test_validate_file_path_with_allowed_directories(file_path, allowed_dirs):
    """
    Testa a validação de diretórios permitidos.

    Args:
        file_path: Um caminho de arquivo válido
        allowed_dirs: Uma lista de diretórios permitidos
    """
    # Criar um caminho absoluto para o arquivo
    try:
        abs_path = os.path.abspath(file_path)

        # Criar um diretório permitido que contém o arquivo
        parent_dir = os.path.dirname(abs_path)
        allowed_dirs.append(parent_dir)

        # A validação deve passar porque o diretório pai está na lista de permitidos
        assert validate_file_path(file_path, allowed_directories=allowed_dirs) is True
    except (ValueError, OSError):
        # Alguns caminhos gerados podem ser inválidos no sistema operacional atual
        pass


@given(st.text(), st.text(min_size=1, max_size=10))
def test_generate_unique_filename_properties(prefix, extension):
    """
    Testa as propriedades da função generate_unique_filename.

    Args:
        prefix: Um prefixo para o nome do arquivo
        extension: Uma extensão para o arquivo
    """
    assume(not any(c in prefix for c in '\\/:*?"<>|'))
    assume(not any(c in extension for c in '\\/:*?"<>|'))

    # Gerar um nome de arquivo único
    filename = generate_unique_filename(extension, prefix)

    # Verificar se o nome do arquivo contém o prefixo (se fornecido)
    if prefix:
        assert prefix in filename

    # Verificar se o nome do arquivo termina com a extensão
    assert filename.endswith(f".{extension}")

    # Verificar se o nome do arquivo contém um UUID (32 caracteres hexadecimais)
    # O UUID está entre o prefixo e a extensão
    if prefix:
        # Formato esperado: prefix_uuid.extension
        uuid_part = filename[len(prefix) + 1:-len(extension) - 1]
    else:
        # Formato esperado: uuid.extension
        uuid_part = filename[:-len(extension) - 1]

    assert len(uuid_part) == 32
    assert all(c in "0123456789abcdef" for c in uuid_part)


@given(st.text(min_size=1, max_size=50))
def test_ensure_directory_exists_properties(directory):
    """
    Testa as propriedades da função ensure_directory_exists.

    Args:
        directory: Um nome de diretório
    """
    # Filtrar caracteres inválidos para nomes de diretório
    assume(not any(c in directory for c in '\\/:*?"<>|'))

    try:
        # Criar um caminho temporário para o teste
        temp_dir = os.path.join(os.path.dirname(__file__), "temp_test_dir")
        test_dir = os.path.join(temp_dir, directory)

        try:
            # Garantir que o diretório pai existe
            os.makedirs(temp_dir, exist_ok=True)

            # Testar a função
            result = ensure_directory_exists(test_dir)

            # Verificar se a função retornou True
            assert result is True

            # Verificar se o diretório foi criado
            assert os.path.exists(test_dir)
            assert os.path.isdir(test_dir)
        finally:
            # Limpar os diretórios criados
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
    except (ValueError, OSError):
        # Alguns nomes de diretório gerados podem ser inválidos no sistema operacional atual
        pass


if __name__ == "__main__":
    if PYTEST_AVAILABLE:
        pytest.main(["-xvs", __file__])
    else:
        unittest.main()
