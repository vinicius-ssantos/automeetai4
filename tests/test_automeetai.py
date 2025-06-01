import unittest
from unittest.mock import Mock, patch
import os
import tempfile

from src.automeetai import AutoMeetAI
from src.models.transcription_result import TranscriptionResult


class TestAutoMeetAI(unittest.TestCase):
    """Test cases for the AutoMeetAI class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock objects for dependencies
        self.config_provider = Mock()
        self.audio_converter = Mock()
        self.transcription_service = Mock()
        self.text_generation_service = Mock()

        # Configure the config provider mock
        self.config_provider.get.side_effect = lambda key, default=None: {
            "large_transcription_threshold": 100,  # Return an integer for this key
            "output_directory": "test_output"
        }.get(key, default)

        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()

        # Create the AutoMeetAI instance with mock dependencies
        self.app = AutoMeetAI(
            config_provider=self.config_provider,
            audio_converter=self.audio_converter,
            transcription_service=self.transcription_service,
            text_generation_service=self.text_generation_service,
            use_cache=False  # Disable cache to ensure audio converter is called
        )

    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('src.automeetai.generate_unique_filename')
    @patch('src.automeetai.validate_file_path')
    @patch('os.path.getsize')
    def test_process_video_success(self, mock_getsize, mock_validate_file_path, mock_generate_filename):
        """Test successful video processing."""
        # Configure mocks
        mock_generate_filename.return_value = os.path.join(self.temp_dir, "test_audio.mp3")
        self.audio_converter.convert.return_value = True
        mock_getsize.return_value = 1024  # Mock file size

        # Create a mock transcript with proper Utterance objects
        from src.models.transcription_result import Utterance
        mock_transcript = TranscriptionResult(
            utterances=[
                Utterance(speaker="Speaker A", text="Hello, this is a test."),
                Utterance(speaker="Speaker B", text="Yes, it is a test.")
            ],
            text="Hello, this is a test. Yes, it is a test.",
            audio_file=os.path.join(self.temp_dir, "test_audio.mp3")
        )
        self.transcription_service.transcribe.return_value = mock_transcript

        # Call the method under test
        result = self.app.process_video("test_video.mp4")

        # Assertions
        self.assertIsNotNone(result)
        self.audio_converter.convert.assert_called_once()
        self.transcription_service.transcribe.assert_called_once()

    @patch('src.automeetai.validate_file_path')
    @patch('src.automeetai.generate_unique_filename')
    def test_process_video_conversion_failure(self, mock_generate_filename, mock_validate_file_path):
        """Test video processing when audio conversion fails."""
        # Configure mocks
        mock_generate_filename.return_value = os.path.join(self.temp_dir, "test_audio.mp3")
        self.audio_converter.convert.return_value = False

        # Call the method under test and expect a ServiceError
        from src.exceptions import ServiceError
        with self.assertRaises(ServiceError) as context:
            self.app.process_video("test_video.mp4")

        # Verify the error message
        self.assertEqual(str(context.exception), "Audio conversion failed")

        # Assertions
        self.audio_converter.convert.assert_called_once()
        self.transcription_service.transcribe.assert_not_called()

    def test_analyze_transcription_success(self):
        """Test successful transcription analysis."""
        # Create a mock transcription result
        transcription = Mock(spec=TranscriptionResult)
        transcription.to_formatted_text.return_value = "Speaker A: Hello\nSpeaker B: Hi"
        transcription.audio_file = os.path.join(self.temp_dir, "test_audio.mp3")
        transcription.utterances = []  # Add empty utterances list to prevent attribute error

        # Configure text generation service mock
        self.text_generation_service.generate.return_value = "This is an analysis of the meeting."

        # Call the method under test
        result = self.app.analyze_transcription(
            transcription=transcription,
            system_prompt="System prompt",
            user_prompt_template="User prompt: {transcription}"
        )

        # Assertions
        self.assertEqual(result, "This is an analysis of the meeting.")
        self.text_generation_service.generate.assert_called_once()
        transcription.to_formatted_text.assert_called_once()


if __name__ == '__main__':
    unittest.main()
