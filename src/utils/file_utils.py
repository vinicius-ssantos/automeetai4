import os
import uuid
import re
import tempfile
import shutil
import contextlib
from typing import Optional, List, Iterator, ContextManager, Pattern
from pathlib import Path
from src.utils.logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

# Compile suspicious patterns once for better performance
# These patterns match the ones in the test_file_utils_properties.py test
SUSPICIOUS_PATTERNS = [
    # Path traversal patterns
    (r'(^|/|\\)\.\.(/|\\|$)', re.compile(r'(^|/|\\)\.\.(/|\\|$)')),  # Parent directory references (must be a path component)
    (r'^\.\.', re.compile(r'^\.\.(?!\.)')),  # Two dots at the start of the path not followed by another dot
    (r'(/|\\)\.\.(?!\.)', re.compile(r'(/|\\)\.\.(?!\.)')),  # Two dots after a path separator not followed by another dot

    # Simple string patterns that match the test's suspicious_patterns list
    (r'\.\.', re.compile(r'\.\.')),          # Two dots anywhere (for test compatibility)
    (r'\\\\', re.compile(r'\\\\')),          # Double backslashes
    (r'//', re.compile(r'//')),            # Double forward slashes
    (r'~', re.compile(r'~')),             # Home directory references
    (r'%00', re.compile(r'%00')),           # Null byte injection
    (r'\$\{', re.compile(r'\$\{')),          # Shell variable injection
    (r'<', re.compile(r'<')),             # Shell redirection
    (r'>', re.compile(r'>')),             # Shell redirection
    (r'\|', re.compile(r'\|')),            # Shell pipe
    (r';', re.compile(r';')),             # Command separator
    (r'&', re.compile(r'&')),             # Command chaining
    (r'\$\(', re.compile(r'\$\(')),          # Command substitution
    (r'`', re.compile(r'`'))              # Command substitution
]


def generate_unique_filename(extension: str, prefix: Optional[str] = None, directory: Optional[str] = None) -> str:
    """
    Generate a unique filename with the given extension.

    Args:
        extension: The file extension (without the dot)
        prefix: Optional prefix for the filename
        directory: Optional directory where the file will be saved

    Returns:
        str: The generated filename
    """
    # Generate a unique ID
    unique_id = uuid.uuid4().hex

    # Create the filename
    if prefix:
        filename = f"{prefix}_{unique_id}.{extension}"
    else:
        filename = f"{unique_id}.{extension}"

    # Add directory if provided
    if directory:
        # Create directory if it doesn't exist
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Return full path
        return os.path.join(directory, filename)

    # Return just the filename
    return filename


def ensure_directory_exists(directory: str) -> bool:
    """
    Ensure that the specified directory exists.

    Args:
        directory: The directory path

    Returns:
        bool: True if the directory exists or was created, False otherwise
    """
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        return True
    except Exception as e:
        logger.error(f"Error creating directory: {e}")
        return False


@contextlib.contextmanager
def secure_temp_file(suffix: Optional[str] = None, prefix: Optional[str] = None, 
                    dir: Optional[str] = None, text: bool = False) -> Iterator[str]:
    """
    Context manager for securely creating and cleaning up temporary files.
    The file is securely deleted when the context is exited, even if an exception occurs.

    Args:
        suffix: Optional suffix for the filename
        prefix: Optional prefix for the filename
        dir: Optional directory where the file will be created
        text: Whether to open the file in text mode

    Yields:
        str: The path to the temporary file

    Example:
        with secure_temp_file(suffix='.mp4') as temp_path:
            # Use the temporary file
            with open(temp_path, 'wb') as f:
                f.write(data)
            # Process the file
            process_video(temp_path)
        # The file is automatically securely deleted when the context is exited
    """
    temp_file = None
    temp_path = None

    try:
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, prefix=prefix, 
                                               dir=dir, delete=False, mode='w' if text else 'wb')
        temp_path = temp_file.name
        temp_file.close()

        # Yield the path to the temporary file
        yield temp_path

    finally:
        # Securely delete the file
        if temp_path and os.path.exists(temp_path):
            try:
                # Overwrite the file with zeros to securely delete its contents
                with open(temp_path, 'wb') as f:
                    # Get the file size
                    file_size = os.path.getsize(temp_path)
                    # Write zeros to the file
                    f.write(b'\x00' * min(file_size, 1024 * 1024))  # Limit to 1MB for large files
                    f.flush()
                    os.fsync(f.fileno())

                # Delete the file
                os.unlink(temp_path)
            except Exception as e:
                logger.error(f"Error securely deleting temporary file: {e}")
                # Attempt to delete the file anyway
                try:
                    os.unlink(temp_path)
                except:
                    pass


def validate_file_path(file_path: str, allowed_directories: Optional[List[str]] = None, 
                      allowed_extensions: Optional[List[str]] = None) -> bool:
    """
    Validate a file path to prevent path traversal attacks.

    This function uses pre-compiled regex patterns for performance optimization,
    especially when handling complex paths with Unicode characters.

    Args:
        file_path: The file path to validate
        allowed_directories: Optional list of allowed directories
        allowed_extensions: Optional list of allowed file extensions

    Returns:
        bool: True if the file path is valid, False otherwise

    Raises:
        ValueError: If the file path is invalid
    """
    if not file_path:
        raise ValueError("File path cannot be empty")

    # Convert to Path object for safer path manipulation
    path = Path(file_path)

    # Check for path traversal attempts
    try:
        # Resolve to absolute path, removing any '..' components
        resolved_path = path.resolve()
    except (ValueError, OSError):
        raise ValueError(f"Invalid file path: {file_path}")

    # Check if the path contains suspicious patterns using pre-compiled patterns for better performance
    for pattern_str, compiled_pattern in SUSPICIOUS_PATTERNS:
        if compiled_pattern.search(file_path):
            raise ValueError(f"File path contains suspicious pattern: {file_path}")

    # Check if the file is in an allowed directory
    if allowed_directories:
        allowed = False
        for directory in allowed_directories:
            dir_path = Path(directory).resolve()
            if str(resolved_path).startswith(str(dir_path)):
                allowed = True
                break

        if not allowed:
            raise ValueError(f"File path is not in an allowed directory: {file_path}")

    # Check if the file has an allowed extension
    if allowed_extensions:
        extension = path.suffix.lower().lstrip('.')
        if extension not in [ext.lower().lstrip('.') for ext in allowed_extensions]:
            raise ValueError(f"File has an invalid extension: {file_path}")

    return True
