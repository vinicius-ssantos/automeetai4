import unittest
from unittest.mock import Mock

from src.adapters.assemblyai_adapter import AssemblyAIAdapter
from src.models.transcription_result import TranscriptionResult


class TestAssemblyAIAdapter(unittest.TestCase):
    """
    Tests for the AssemblyAIAdapter.
    """

    def test_convert_with_none_utterances(self):
        """Test that convert handles None utterances correctly."""
        # Create a mock transcript with None utterances
        mock_transcript = Mock()
        mock_transcript.utterances = None
        mock_transcript.text = "Test transcript"

        # Call the convert method
        result = AssemblyAIAdapter.convert(mock_transcript, "test_audio.mp3")

        # Verify that a TranscriptionResult is returned with empty utterances
        self.assertIsInstance(result, TranscriptionResult)
        self.assertEqual(result.utterances, [])
        self.assertEqual(result.text, "Test transcript")
        self.assertEqual(result.audio_file, "test_audio.mp3")

    def test_convert_with_empty_utterances(self):
        """Test that convert handles empty utterances correctly."""
        # Create a mock transcript with empty utterances
        mock_transcript = Mock()
        mock_transcript.utterances = []
        mock_transcript.text = "Test transcript"

        # Call the convert method
        result = AssemblyAIAdapter.convert(mock_transcript, "test_audio.mp3")

        # Verify that a TranscriptionResult is returned with empty utterances
        self.assertIsInstance(result, TranscriptionResult)
        self.assertEqual(result.utterances, [])
        self.assertEqual(result.text, "Test transcript")
        self.assertEqual(result.audio_file, "test_audio.mp3")

    def test_convert_with_valid_utterances(self):
        """Test that convert handles valid utterances correctly."""
        # Create a mock utterance
        mock_utterance = Mock()
        mock_utterance.speaker = 1
        mock_utterance.text = "Hello, world!"
        mock_utterance.start = 1000  # 1 second in milliseconds
        mock_utterance.end = 2000    # 2 seconds in milliseconds

        # Create a mock transcript with valid utterances
        mock_transcript = Mock()
        mock_transcript.utterances = [mock_utterance]
        mock_transcript.text = "Test transcript"

        # Call the convert method
        result = AssemblyAIAdapter.convert(mock_transcript, "test_audio.mp3")

        # Verify that a TranscriptionResult is returned with the correct utterances
        self.assertIsInstance(result, TranscriptionResult)
        self.assertEqual(len(result.utterances), 1)
        self.assertEqual(result.utterances[0].speaker, "Speaker 1")
        self.assertEqual(result.utterances[0].text, "Hello, world!")
        self.assertEqual(result.utterances[0].start, 1.0)  # Converted from ms to seconds
        self.assertEqual(result.utterances[0].end, 2.0)    # Converted from ms to seconds
        self.assertEqual(result.text, "Test transcript")
        self.assertEqual(result.audio_file, "test_audio.mp3")

    def test_convert_with_none_transcript(self):
        """Test that convert handles None transcript correctly."""
        # Call the convert method with None transcript
        result = AssemblyAIAdapter.convert(None, "test_audio.mp3")

        # Verify that None is returned
        self.assertIsNone(result)

    def test_convert_with_exception_transcript(self):
        """Test that convert handles Exception transcript correctly."""
        # Call the convert method with an Exception transcript
        result = AssemblyAIAdapter.convert(Exception("Test exception"), "test_audio.mp3")

        # Verify that None is returned
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()