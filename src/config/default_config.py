"""
Default configuration values for the application.
These values can be overridden by environment variables or at runtime.
"""

# AssemblyAI API configuration
# Must be set via environment variable AUTOMEETAI_ASSEMBLYAI_API_KEY
ASSEMBLYAI_API_KEY = None

# OpenAI API configuration
# Must be set via environment variable AUTOMEETAI_OPENAI_API_KEY
OPENAI_API_KEY = None
OPENAI_MODEL = "gpt-4o-2024-08-06"

# REST API authentication
# Must be set via environment variable AUTOMEETAI_API_AUTH_TOKEN
API_AUTH_TOKEN = None

# Whisper API configuration
# Uses the same API key as OpenAI (AUTOMEETAI_OPENAI_API_KEY)
WHISPER_MODEL = "whisper-1"
WHISPER_LANGUAGE = "pt"  # Language code for transcription
WHISPER_TEMPERATURE = 0  # Lower values are more deterministic
WHISPER_RESPONSE_FORMAT = "verbose_json"  # Returns timestamps and segments

# Transcription configuration
DEFAULT_LANGUAGE_CODE = "pt"
DEFAULT_SPEAKER_LABELS = True
DEFAULT_SPEAKERS_EXPECTED = 2

# File paths
DEFAULT_OUTPUT_DIRECTORY = "output"

# Audio conversion configuration
DEFAULT_ALLOWED_INPUT_EXTENSIONS = ["mp4", "avi", "mov", "mkv", "wmv", "flv", "webm", "mp3", "wav", "ogg", "flac", "m4v", "3gp", "mpg", "mpeg", "ts", "m2ts", "vob", "ogv", "divx", "aac", "m4a", "wma", "aiff", "ac3", "amr"]
DEFAULT_ALLOWED_OUTPUT_EXTENSIONS = ["mp3", "wav", "ogg", "flac", "aac", "m4a", "wma", "aiff", "ac3"]
DEFAULT_AUDIO_BITRATE = "128k"
DEFAULT_AUDIO_FPS = 44100  # Sample rate in Hz

# Large file optimization configuration
DEFAULT_LARGE_FILE_THRESHOLD = 100 * 1024 * 1024  # 100 MB
DEFAULT_CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB
DEFAULT_BUFFER_SIZE = 1024 * 1024  # 1 MB
DEFAULT_LARGE_FILE_BITRATE = "96k"  # Lower bitrate for large files
DEFAULT_LARGE_FILE_FPS = 22050  # Lower sample rate for large files
DEFAULT_TEMP_DIR = None  # Use system default temp directory
DEFAULT_USE_STREAMING_FOR_LARGE_FILES = True  # Use streaming for large files
DEFAULT_STREAMING_CHUNK_SIZE = 4096  # Chunk size for streaming in bytes

# Transcription result optimization configuration
DEFAULT_USE_OPTIMIZED_TRANSCRIPTION_RESULT = True  # Use optimized transcription result model
DEFAULT_LARGE_TRANSCRIPTION_THRESHOLD = 1000  # Number of utterances to consider a transcription as "large"
DEFAULT_UTTERANCE_CHUNK_SIZE = 100  # Number of utterances to load at once in optimized model

# Lazy loading configuration for text processing
DEFAULT_USE_LAZY_TEXT_PROCESSING = True  # Use lazy loading for text processing
DEFAULT_TEXT_PROCESSING_CHUNK_SIZE = 1000  # Number of characters to process at once
DEFAULT_TEXT_PROCESSING_MAX_CHUNKS = None  # Maximum number of chunks to process (None for all)

# Parallel processing configuration
DEFAULT_MAX_WORKERS = 4  # Maximum number of parallel workers
DEFAULT_PARALLEL_PROCESSING = True  # Enable parallel processing by default
DEFAULT_CHUNK_SIZE_PARALLEL = 2  # Number of files to process in each worker

# Rate limiting configuration
# AssemblyAI rate limits: https://www.assemblyai.com/docs/api-reference/rate-limits
# Default: 10 requests per minute (0.167 per second)
ASSEMBLYAI_RATE_LIMIT = 0.167
ASSEMBLYAI_RATE_LIMIT_PER = 1.0  # 1 second
ASSEMBLYAI_RATE_LIMIT_BURST = 5  # Allow bursts of up to 5 requests

# OpenAI rate limits: https://platform.openai.com/docs/guides/rate-limits
# Default: 3 requests per minute for free tier (0.05 per second)
OPENAI_RATE_LIMIT = 0.05
OPENAI_RATE_LIMIT_PER = 1.0  # 1 second
OPENAI_RATE_LIMIT_BURST = 3  # Allow bursts of up to 3 requests
