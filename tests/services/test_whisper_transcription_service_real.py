import os
import pytest
from src.services.whisper_transcription_service import WhisperTranscriptionService
from src.interfaces.config_provider import ConfigProvider
from src.models.transcription_result import TranscriptionResult

class TestConfigProvider(ConfigProvider):
    """A simple config provider for testing that reads from environment variables."""
    
    def get(self, key, default=None):
        """Get a configuration value."""
        import os
        return os.environ.get(key, default)


@pytest.mark.manual
class TestWhisperTranscriptionServiceReal:
    """
    Tests for the WhisperTranscriptionService using the real API.
    
    These tests call the real OpenAI Whisper API and consume credits.
    They are marked with @pytest.mark.manual and will be skipped by default.
    To run these tests, use: pytest tests/test_whisper_transcription_service_real.py --manual
    """
    
    def setup_method(self):
        """Set up the test environment."""
        # Use a config provider that reads from environment variables
        self.config_provider = TestConfigProvider()
        
        # Create the service
        self.service = WhisperTranscriptionService(self.config_provider)
        
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
    
    def test_transcribe_real_audio(self):
        """Test transcribing a real audio file using the OpenAI Whisper API."""
        # Skip if no API key is set
        api_key = os.environ.get("AUTOMEETAI_OPENAI_API_KEY")
        if not api_key:
            pytest.skip("AUTOMEETAI_OPENAI_API_KEY environment variable not set")
        
        # Use the first sample audio file
        audio_file = self.sample_audio_files[0]
        
        # Transcribe the audio file
        result = self.service.transcribe(audio_file)
        
        # Verify the result
        assert result is not None
        assert isinstance(result, TranscriptionResult)
        assert result.text is not None
        assert len(result.text) > 0
        
        # Print the transcription result for manual verification
        print(f"\nTranscription result for {os.path.basename(audio_file)}:")
        print(f"Text: {result.text[:100]}...")  # Print first 100 chars
    
    def test_transcribe_with_custom_config(self):
        """Test transcribing with custom configuration using the OpenAI Whisper API."""
        # Skip if no API key is set
        api_key = os.environ.get("AUTOMEETAI_OPENAI_API_KEY")
        if not api_key:
            pytest.skip("AUTOMEETAI_OPENAI_API_KEY environment variable not set")
        
        # Use the first sample audio file
        audio_file = self.sample_audio_files[0]
        
        # Define custom configuration
        config = {
            "temperature": 0.3,  # Lower temperature for more deterministic results
            "language": "en"     # Force English language
        }
        
        # Transcribe the audio file with custom configuration
        result = self.service.transcribe(audio_file, config=config)
        
        # Verify the result
        assert result is not None
        assert isinstance(result, TranscriptionResult)
        assert result.text is not None
        assert len(result.text) > 0
        
        # Print the transcription result for manual verification
        print(f"\nTranscription result with custom config for {os.path.basename(audio_file)}:")
        print(f"Text: {result.text[:100]}...")  # Print first 100 chars