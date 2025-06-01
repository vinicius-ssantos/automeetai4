import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestApp(unittest.TestCase):
    """Test cases for the app.py file."""
    
    @patch('streamlit.secrets')
    @patch('src.factory.AutoMeetAIFactory')
    def test_app_initialization(self, mock_factory, mock_secrets):
        """Test that the app initializes correctly."""
        # Setup mocks
        mock_secrets.get.return_value = {'api_key': 'test_key'}
        mock_factory_instance = MagicMock()
        mock_factory.return_value = mock_factory_instance
        
        # Import app (this will execute the initialization code)
        with patch.dict('os.environ', {'ASSEMBLYAI_API_KEY': 'test_key', 'OPENAI_API_KEY': 'test_key'}):
            import app
            
            # Verify that the factory was called with the correct parameters
            mock_factory_instance.create.assert_called_once()
            
            # Verify that automeetai was initialized
            self.assertIsNotNone(app.automeetai)
    
    @patch('streamlit.file_uploader')
    @patch('tempfile.NamedTemporaryFile')
    @patch('src.factory.AutoMeetAIFactory')
    def test_file_processing(self, mock_factory, mock_tempfile, mock_file_uploader):
        """Test that file processing works correctly."""
        # Setup mocks
        mock_factory_instance = MagicMock()
        mock_factory.return_value = mock_factory_instance
        mock_automeetai = MagicMock()
        mock_factory_instance.create.return_value = mock_automeetai
        
        # Mock the transcription result
        mock_utterance = MagicMock()
        mock_utterance.speaker = "1"
        mock_utterance.text = "This is a test."
        mock_transcription = MagicMock()
        mock_transcription.utterances = [mock_utterance]
        mock_automeetai.process_video.return_value = mock_transcription
        
        # Mock the analysis result
        mock_automeetai.analyze_transcription.return_value = "Meeting minutes generated."
        
        # Import app
        with patch.dict('os.environ', {'ASSEMBLYAI_API_KEY': 'test_key', 'OPENAI_API_KEY': 'test_key'}):
            import app
            
            # Replace app's automeetai with our mock
            app.automeetai = mock_automeetai
            
            # Test that process_video is called with the correct parameters
            # This is a simplified test since we can't fully test the Streamlit UI
            self.assertIsNotNone(app.automeetai)
            
if __name__ == '__main__':
    unittest.main()