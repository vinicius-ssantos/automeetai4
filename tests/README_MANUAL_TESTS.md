# Manual API Tests

This directory contains tests that call real APIs and consume credits. These tests are marked with `@pytest.mark.manual` and are skipped by default to prevent accidental credit consumption.

## Prerequisites

Before running these tests, you need to set the following environment variables with your API keys:

- `AUTOMEETAI_ASSEMBLYAI_API_KEY` - Your AssemblyAI API key
- `AUTOMEETAI_OPENAI_API_KEY` - Your OpenAI API key

## Running Manual Tests

To run these tests, you need to use the `--manual` flag with pytest:

```bash
# Run all manual tests
pytest tests/ --manual

# Run a specific manual test file
pytest tests/test_assemblyai_transcription_service_real.py --manual

# Run a specific test
pytest tests/test_openai_text_generation_service_real.py::TestOpenAITextGenerationServiceReal::test_generate_real_text --manual
```

## Available Manual Tests

The following manual tests are available:

### AssemblyAI Transcription Service

Tests for the AssemblyAI batch transcription service:

```bash
pytest tests/test_assemblyai_transcription_service_real.py --manual
```

### AssemblyAI Streaming Transcription Service

Tests for the AssemblyAI streaming transcription service:

```bash
pytest tests/test_assemblyai_streaming_transcription_service_real.py --manual
```

### OpenAI Text Generation Service

Tests for the OpenAI text generation service:

```bash
pytest tests/test_openai_text_generation_service_real.py --manual
```

### Whisper Transcription Service

Tests for the OpenAI Whisper transcription service:

```bash
pytest tests/test_whisper_transcription_service_real.py --manual
```

## Warning

Running these tests will consume real API credits. Make sure you have sufficient credits in your accounts before running them.