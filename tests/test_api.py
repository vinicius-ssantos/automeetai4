import os
import sys
import unittest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

# Configure API authentication for tests
os.environ["AUTOMEETAI_API_AUTH_TOKEN"] = "testtoken123"

# Allow importing the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import api  # noqa: E402


class TestAPI(unittest.TestCase):
    """Tests for the REST API."""

    def setUp(self) -> None:
        """Patch the AutoMeetAI instance used by the API."""
        self.mock_app = MagicMock()
        api.automeetai = self.mock_app
        self.client = TestClient(api.app)

    def test_health_endpoint(self):
        """Ensure the health endpoint returns status ok."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_transcriptions_endpoint(self):
        """Verify that the transcription endpoint processes files."""
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
            params={
                "speaker_labels": "false",
                "speakers_expected": "3",
                "language_code": "en",
            },
            headers={"X-API-Key": "testtoken123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["text"], "hello")
        self.mock_app.process_video.assert_called_once()
        cfg = self.mock_app.process_video.call_args.kwargs.get("transcription_config")
        self.assertEqual(cfg["speaker_labels"], False)
        self.assertEqual(cfg["speakers_expected"], 3)
        self.assertEqual(cfg["language_code"], "en")

    def test_analysis_endpoint(self):
        """Verify that the analysis endpoint returns data."""
        self.mock_app.analyze_transcription.return_value = "summary"

        response = self.client.post(
            "/analysis",
            json={"text": "hello", "system_prompt": "sys", "user_prompt": "user {transcription}"},
            headers={"X-API-Key": "testtoken123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"analysis": "summary"})
        self.mock_app.analyze_transcription.assert_called_once()

    def test_missing_api_key(self):
        """Requests without the API key should fail."""
        response = self.client.post("/analysis", json={"text": "hello"})
        self.assertEqual(response.status_code, 401)

    def test_graphql_health(self):
        """Query health over GraphQL."""
        response = self.client.post(
            "/graphql",
            json={"query": "{ health }"},
            headers={"X-API-Key": "testtoken123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["health"], "ok")

    def test_graphql_analyze(self):
        """Mutation analyze over GraphQL."""
        self.mock_app.analyze_transcription.return_value = "summary"
        mutation = "mutation { analyze(text: \"hello\") }"
        response = self.client.post(
            "/graphql",
            json={"query": mutation},
            headers={"X-API-Key": "testtoken123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["analyze"], "summary")


if __name__ == "__main__":
    unittest.main()
