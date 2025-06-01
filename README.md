# AutoMeetAI

AutoMeetAI is a Python application that automates the process of transcribing and analyzing meeting recordings. It follows SOLID principles and best practices for maintainable and extensible code.

## Features

- Convert video files (MP4) to audio files (MP3)
- Transcribe audio files with speaker identification
- Analyze transcriptions using AI to extract insights
- Command-line interface for easy use
- Modular architecture following SOLID principles

## Architecture

The project follows SOLID principles:

- **Single Responsibility Principle**: Each class has a single responsibility
- **Open/Closed Principle**: The code is open for extension but closed for modification
- **Liskov Substitution Principle**: Implementations can be substituted without affecting the behavior
- **Interface Segregation Principle**: Interfaces are specific to client needs
- **Dependency Inversion Principle**: High-level modules depend on abstractions, not concrete implementations

### Project Structure

```
automeetai/
├── src/
│   ├── config/           # Configuration management
│   ├── interfaces/       # Abstract interfaces
│   ├── models/           # Data models
│   ├── services/         # Service implementations
│   ├── utils/            # Utility functions
│   ├── automeetai.py     # Main application class
│   └── factory.py        # Factory for creating the application
└── main.py               # Command-line interface
```

## Requirements

- Python 3.8+
- AssemblyAI API key
- OpenAI API key (optional, for analysis)
- Dependencies: moviepy, assemblyai, openai

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install moviepy assemblyai openai
   ```
3. Set up API keys:
   - Set environment variable `AUTOMEETAI_ASSEMBLYAI_API_KEY` with your AssemblyAI API key
   - Set environment variable `AUTOMEETAI_OPENAI_API_KEY` with your OpenAI API key (optional)

## Usage

### Command Line

```bash
python main.py <video_file> [--analyze] [--save-audio] [--assemblyai-key KEY] [--openai-key KEY]
```

Options:
- `--analyze`: Analyze the transcription using AI
- `--save-audio`: Save the intermediate audio file
- `--assemblyai-key KEY`: AssemblyAI API key (overrides environment variable)
- `--openai-key KEY`: OpenAI API key (overrides environment variable)

Example:
```bash
python main.py entrevista.mp4 --analyze
```

### Programmatic Usage

```python
from src.factory import AutoMeetAIFactory

# Create the application
factory = AutoMeetAIFactory()
app = factory.create(
    assemblyai_api_key="your_assemblyai_api_key",
    openai_api_key="your_openai_api_key"
)

# Process a video file
transcription = app.process_video("path/to/video.mp4")

# Analyze the transcription
analysis = app.analyze_transcription(
    transcription=transcription,
    system_prompt="You are a helpful assistant that analyzes meeting transcriptions.",
    user_prompt_template="Please analyze the following meeting transcription:\n\n{transcription}"
)
```

## Extending the Application

The modular architecture makes it easy to extend the application:

1. To add a new audio converter, implement the `AudioConverter` interface
2. To add a new transcription service, implement the `TranscriptionService` interface
3. To add a new text generation service, implement the `TextGenerationService` interface
4. To add a new configuration provider, implement the `ConfigProvider` interface

## License

This project is licensed under the MIT License.
