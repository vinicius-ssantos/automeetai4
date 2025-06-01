import os
import pytest
import time
from src.services.assemblyai_streaming_transcription_service import AssemblyAIStreamingTranscriptionService
from src.interfaces.config_provider import ConfigProvider
from src.models.transcription_result import TranscriptionResult

class TestConfigProvider(ConfigProvider):
    """A simple config provider for testing that reads from environment variables."""

    def get(self, key, default=None):
        """Get a configuration value."""
        import os
        return os.environ.get(key, default)

    def set(self, key, value):
        """Set a configuration value."""
        # This is a test implementation that doesn't actually set environment variables
        # It's just here to satisfy the interface
        pass


@pytest.mark.manual
class TestAssemblyAIStreamingTranscriptionServiceReal:
    """
    Tests for the AssemblyAIStreamingTranscriptionService using the real API.

    These tests call the real AssemblyAI streaming API and consume credits.
    They are marked with @pytest.mark.manual and will be skipped by default.
    To run these tests, use: pytest tests/test_assemblyai_streaming_transcription_service_real.py --manual
    """

    def setup_method(self):
        """Set up the test environment."""
        # Use a config provider that reads from environment variables
        self.config_provider = TestConfigProvider()

        # Create the service
        self.service = AssemblyAIStreamingTranscriptionService(self.config_provider)

        # Find a sample audio file
        self.sample_audio_files = []
        output_dir = os.path.join(os.getcwd(), "output")
        if os.path.exists(output_dir):
            for file in os.listdir(output_dir):
                if file.endswith(".mp3"):
                    self.sample_audio_files.append(os.path.join(output_dir, file))

        # Skip tests if no audio files are found
        if not self.sample_audio_files:
            pytest.skip("No sample audio files found in the output directory")

    def test_stream_file(self):
        """Test streaming a file using the AssemblyAI streaming API."""
        # Skip if no API key is set
        api_key = os.environ.get("AUTOMEETAI_ASSEMBLYAI_API_KEY")
        if not api_key:
            pytest.skip("AUTOMEETAI_ASSEMBLYAI_API_KEY environment variable not set")

        # Use the first sample audio file
        audio_file = self.sample_audio_files[0]

        # Store partial results
        partial_results = []

        # Callback function for partial results
        def result_callback(result):
            partial_results.append(result)
            print(f"Partial result: {result.get('text', '')[:50]}...")

        # Progress callback function
        def progress_callback(progress, message):
            print(f"Progress: {progress}% - {message}")

        # Stream the file
        result = self.service.stream_file(
            audio_file=audio_file,
            callback=result_callback,
            progress_callback=progress_callback
        )

        # Verify the result
        assert result is not None
        assert isinstance(result, TranscriptionResult)
        assert result.text is not None
        assert len(result.text) > 0

        # Print the transcription result for manual verification
        print(f"\nFinal transcription result for {os.path.basename(audio_file)}:")
        print(f"Text: {result.text[:100]}...")  # Print first 100 chars

        # Verify that we received partial results
        assert len(partial_results) > 0

    def test_start_stop_streaming(self):
        """Test starting and stopping a streaming session."""
        # Skip if no API key is set
        api_key = os.environ.get("AUTOMEETAI_ASSEMBLYAI_API_KEY")
        if not api_key:
            pytest.skip("AUTOMEETAI_ASSEMBLYAI_API_KEY environment variable not set")

        # Start streaming
        success = self.service.start_streaming()
        assert success, "Failed to start streaming session"

        # Verify that streaming is active
        assert self.service.is_streaming(), "Streaming session should be active"

        # Wait a moment
        time.sleep(1)

        # Stop streaming
        result = self.service.stop_streaming()

        # Verify that streaming is no longer active
        assert not self.service.is_streaming(), "Streaming session should no longer be active"

        # The result might be None or an empty TranscriptionResult since we didn't send any audio
        if result is not None:
            assert isinstance(result, TranscriptionResult)
