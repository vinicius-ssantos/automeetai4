# AutoMeetAI Development Guidelines

This document provides guidelines and information for developers working on the AutoMeetAI project.

## Build/Configuration Instructions

### Environment Setup

1. **Python Version**: AutoMeetAI requires Python 3.8 or higher.

2. **Virtual Environment**: It's recommended to use a virtual environment for development:
   ```bash
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On Unix/MacOS
   source .venv/bin/activate
   ```

3. **Dependencies Installation**:
   ```bash
   # Install main dependencies
   pip install -r requirements.txt
   
   # Install development dependencies
   pip install -r requirements-dev.txt
   ```

### API Keys Configuration

AutoMeetAI requires API keys for external services. These can be configured in several ways:

1. **Environment Variables**:
   ```bash
   # Windows
   set AUTOMEETAI_ASSEMBLYAI_API_KEY=your_assemblyai_key
   set AUTOMEETAI_OPENAI_API_KEY=your_openai_key
   
   # Unix/MacOS
   export AUTOMEETAI_ASSEMBLYAI_API_KEY=your_assemblyai_key
   export AUTOMEETAI_OPENAI_API_KEY=your_openai_key
   ```

2. **User Preferences File**:
   Create a `user_preferences.json` file in the project root with the following structure:
   ```json
   {
     "assemblyai_api_key": "your_assemblyai_key",
     "openai_api_key": "your_openai_key",
     "output_directory": "output",
     "default_language_code": "pt-br",
     "default_speaker_labels": true,
     "default_speakers_expected": 2,
     "openai_model": "gpt-3.5-turbo"
   }
   ```

3. **Streamlit Secrets** (for Streamlit app):
   If using the Streamlit interface, you can configure secrets in `.streamlit/secrets.toml`.

### Configuration Precedence

The configuration system follows this precedence order (highest to lowest):
1. Command-line arguments
2. Environment variables
3. User preferences file
4. Default values

## Testing Information

### Test Structure

Tests are organized to mirror the project structure:
```
tests/
├── adapters/       # Tests for adapter implementations
├── config/         # Tests for configuration components
├── fixtures/       # Reusable test fixtures
├── formatters/     # Tests for formatters
├── interfaces/     # Tests for interfaces
├── mocks/          # Mock objects for testing
├── models/         # Tests for data models
├── services/       # Tests for service implementations
├── utils/          # Tests for utility functions
└── conftest.py     # Global pytest fixtures
```

### Running Tests

1. **Running All Tests**:
   ```bash
   python -m pytest
   ```

2. **Running Tests with Coverage**:
   ```bash
   python tests/run_tests_with_coverage.py
   # Or with specific options
   python tests/run_tests_with_coverage.py --html --min-coverage 80
   ```

3. **Running Specific Tests**:
   ```bash
   # Run tests in a specific directory
   python -m pytest tests/utils/
   
   # Run a specific test file
   python -m pytest tests/utils/test_file_utils_properties.py
   
   # Run a specific test class
   python -m pytest tests/utils/test_secure_temp_file.py::TestSecureTempFile
   
   # Run a specific test method
   python -m pytest tests/utils/test_secure_temp_file.py::TestSecureTempFile::test_secure_temp_file_creates_and_deletes
   ```

4. **Running Tests with Verbosity**:
   ```bash
   python -m pytest -v
   ```

5. **Running Tests that Call Real APIs**:
   ```bash
   python -m pytest --manual
   ```

### Adding New Tests

1. **Test File Naming**: Name test files with the prefix `test_` followed by the name of the module being tested.

2. **Test Location**: Place tests in the appropriate subdirectory of the `tests` directory, mirroring the project structure.

3. **Test Frameworks**: The project supports both unittest and pytest. Most tests use unittest with pytest as the test runner.

4. **Property-Based Testing**: For functions with complex input/output relationships, consider using property-based testing with Hypothesis.

5. **Test Example**:
   ```python
   import unittest
   from src.utils.file_utils import secure_temp_file
   
   class TestSecureTempFile(unittest.TestCase):
       def test_secure_temp_file_creates_and_deletes(self):
           with secure_temp_file(suffix='.txt') as temp_path:
               # Verify the file exists
               self.assertTrue(os.path.exists(temp_path))
               # Write some data to the file
               with open(temp_path, 'w') as f:
                   f.write('test data')
           # Verify the file is deleted after the context is exited
           self.assertFalse(os.path.exists(temp_path))
   ```

6. **Test Fixtures**: Use the fixtures in `tests/fixtures` for common test setup. For example, to create a test configuration:
   ```python
   from tests.fixtures.config_fixtures import TestConfigBuilder
   
   # Create a test configuration
   config = TestConfigBuilder() \
       .with_api_keys() \
       .with_output_directory() \
       .with_transcription_settings() \
       .build()
   ```

7. **Mocking External Services**: Use unittest.mock to mock external services:
   ```python
   from unittest.mock import patch, MagicMock
   
   @patch('src.services.openai_text_generation_service.OpenAI')
   def test_generate_text(self, mock_openai):
       # Configure the mock
       mock_client = MagicMock()
       mock_openai.return_value = mock_client
       # Test the function
       # ...
   ```

8. **Manual Tests**: For tests that call real APIs and consume credits, mark them with the `@pytest.mark.manual` decorator:
   ```python
   import pytest
   
   @pytest.mark.manual
   def test_real_api_call():
       # This test will only run when the --manual flag is provided
       # ...
   ```

## Additional Development Information

### Code Style

1. **Type Hints**: Use type hints for function parameters and return values.

2. **Docstrings**: Use Google-style docstrings for all classes and functions.

3. **SOLID Principles**: Follow SOLID principles in your code:
   - Single Responsibility Principle
   - Open/Closed Principle
   - Liskov Substitution Principle
   - Interface Segregation Principle
   - Dependency Inversion Principle

4. **Error Handling**: Use appropriate error handling with specific exception types and meaningful error messages.

### Project Architecture

1. **Interfaces**: Define interfaces in the `src/interfaces` directory. All implementations should adhere to these interfaces.

2. **Configuration**: Use the configuration system in `src/config` for accessing configuration values.

3. **Factory Pattern**: Use the factory pattern for creating complex objects, as demonstrated in `src/factory.py`.

4. **Dependency Injection**: Use dependency injection to provide dependencies to classes rather than having them create their own dependencies.

### Extending the Application

1. **Adding a New Audio Converter**: Implement the `AudioConverter` interface in `src/interfaces/audio_converter.py`.

2. **Adding a New Transcription Service**: Implement the `TranscriptionService` interface in `src/interfaces/transcription_service.py`.

3. **Adding a New Text Generation Service**: Implement the `TextGenerationService` interface in `src/interfaces/text_generation_service.py`.

4. **Adding a New Configuration Provider**: Implement the `ConfigProvider` interface in `src/interfaces/config_provider.py`.

### Debugging

1. **Logging**: Use the logging utilities in `src/utils/logging.py` for consistent logging:
   ```python
   from src.utils.logging import get_logger
   
   logger = get_logger(__name__)
   logger.debug("Debug message")
   logger.info("Info message")
   logger.warning("Warning message")
   logger.error("Error message")
   ```

2. **Environment Variables for Debugging**:
   - Set `AUTOMEETAI_LOG_LEVEL=DEBUG` for more verbose logging
   - Set `AUTOMEETAI_LOG_FILE=path/to/log.txt` to log to a file

### Security Considerations

1. **API Keys**: Never commit API keys to the repository. Use environment variables or user preferences.

2. **File Path Validation**: Use the `validate_file_path` function in `src/utils/file_utils.py` to validate file paths and prevent path traversal attacks.

3. **Secure Temporary Files**: Use the `secure_temp_file` context manager in `src/utils/file_utils.py` for securely creating and cleaning up temporary files.