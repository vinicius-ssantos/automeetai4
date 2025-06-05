import os
import sys
import unittest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

# Configure API authentication for tests
os.environ["AUTOMEETAI_API_AUTH_TOKEN"] = "testtoken123"

# Allow importing the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.microservices import transcription_service, analysis_service  # noqa: E402


class TestTranscriptionService(unittest.TestCase):
    """Tests for the transcription microservice."""

    def setUp(self) -> None:
        """Patch the AutoMeetAI instance used by the service."""
        self.mock_app = MagicMock()
        transcription_service.automeetai = self.mock_app
        self.client = TestClient(transcription_service.app)

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_transcribe(self):
        from src.models.transcription_result import TranscriptionResult, Utterance

        transcription = TranscriptionResult(
            utterances=[Utterance(speaker="1", text="hello")],
            text="hello",
            audio_file="file.mp3",
        )
        self.mock_app.process_video.return_value = transcription

        response = self.client.post(
            "/transcriptions",
            files={"file": ("test.mp4", b"data", "video/mp4")},
            params={"speaker_labels": "false"},
            headers={"X-API-Key": "testtoken123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["text"], "hello")
        self.mock_app.process_video.assert_called_once()


class TestAnalysisService(unittest.TestCase):
    """Tests for the analysis microservice."""

    def setUp(self) -> None:
        self.mock_app = MagicMock()
        analysis_service.automeetai = self.mock_app
        self.client = TestClient(analysis_service.app)

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_analyze(self):
        self.mock_app.analyze_transcription.return_value = "summary"
        response = self.client.post(
            "/analysis",
            json={"text": "hello"},
            headers={"X-API-Key": "testtoken123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"analysis": "summary"})
        self.mock_app.analyze_transcription.assert_called_once()


if __name__ == "__main__":
    unittest.main()
