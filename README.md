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

## Docker

A `Dockerfile` is provided to build a container image. The accompanying
`.dockerignore` excludes `tests/`, `docs/`, `.git/`, `cache/` and temporary
files so the build context remains small. The image installs dependencies from
`requirements.txt` and creates a non-root user called `appuser` for safer
execution.

Build the image with:

```bash
docker build -t automeetai .
```

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

### REST API

You can also interact with AutoMeetAI through a simple REST API built with
FastAPI. The API requires an authentication token provided via the
`AUTOMEETAI_API_AUTH_TOKEN` environment variable. Clients must send this token in
the `X-API-Key` header when calling protected endpoints.

After installing the dependencies, run:

```bash
uvicorn api:app --reload
```

This will start a server on `http://localhost:8000` exposing the following
endpoints:

- `GET /health` – basic health check
- `POST /transcriptions` – upload a video file and get its transcription
- `POST /analysis` – analyze a transcription text
- `POST /graphql` – GraphQL endpoint with a playground


The `/transcriptions` endpoint accepts optional query parameters to control the
transcription process:

- `speaker_labels` – whether to enable speaker diarization (default `true`)
- `speakers_expected` – expected number of speakers (default `2`)
- `language_code` – ISO code of the audio language (default `pt`)

## Docker

Docker makes it easy to run AutoMeetAI without installing Python or dependencies.

Build the image and start the API with Docker Compose:

```bash
docker compose up --build
```

Then access the API at `http://localhost:8000`. Set the `AUTOMEETAI_API_AUTH_TOKEN` environment variable in `docker-compose.yml` to secure your deployment.


## Extending the Application

The modular architecture makes it easy to extend the application:

1. To add a new audio converter, implement the `AudioConverter` interface
2. To add a new transcription service, implement the `TranscriptionService` interface
3. To add a new text generation service, implement the `TextGenerationService` interface
4. To add a new configuration provider, implement the `ConfigProvider` interface

## License

This project is licensed under the MIT License.
