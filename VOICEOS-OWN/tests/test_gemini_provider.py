from unittest.mock import MagicMock, patch
import pytest
from ai.gemini_provider import GeminiProvider

def test_gemini_initialization_empty():
    provider = GeminiProvider(api_key="")
    assert not provider.api_key
    res = provider.test_connection()
    assert not res["success"]
    assert "No API key configured" in res["error"]

def test_gemini_missing_key_generation():
    provider = GeminiProvider(api_key="")
    chunks = list(provider.generate_response(prompt="Hello"))
    assert len(chunks) == 1
    assert chunks[0]["type"] == "error"
    assert "Gemini API key is not configured" in chunks[0]["content"]

@patch("google.genai.Client")
def test_gemini_successful_test_connection_genai(mock_client_cls):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = MagicMock(text="pong")
    mock_client_cls.return_value = mock_client

    provider = GeminiProvider(api_key="AIzaSyValidDummyKey123")
    res = provider.test_connection()
    assert res["success"] is True
    assert "Connected successfully" in res["message"]

@patch("google.genai.Client")
def test_gemini_invalid_key_error(mock_client_cls):
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("API_KEY_INVALID: key is not valid")
    mock_client_cls.return_value = mock_client

    provider = GeminiProvider(api_key="AIzaSyInvalidKey")
    res = provider.test_connection()
    assert res["success"] is False
    assert "Invalid Gemini API Key" in res["error"]

@patch("google.genai.Client")
def test_gemini_streaming_generation(mock_client_cls):
    mock_client = MagicMock()
    chunk1 = MagicMock(text="Hello ", function_calls=None)
    chunk2 = MagicMock(text="world!", function_calls=None)
    mock_client.models.generate_content_stream.return_value = [chunk1, chunk2]
    mock_client_cls.return_value = mock_client

    provider = GeminiProvider(api_key="AIzaSyDummyKey")
    events = list(provider.generate_response("Hi", stream=True))

    chunks = [e["content"] for e in events if e["type"] == "chunk"]
    assert chunks == ["Hello ", "world!"]
    complete_events = [e for e in events if e["type"] == "complete"]
    assert len(complete_events) == 1
    assert complete_events[0]["content"] == "Hello world!"

@patch("google.genai.Client")
def test_gemini_omniroute_silent_fallback(mock_client_cls):
    """
    Tests that if the primary model fails (e.g. 404 / 429), Omniroute
    silently retries the next candidate model without sending any error
    chunks to the user.
    """
    mock_client = MagicMock()

    def mock_stream(model, contents, config):
        if model == "gemini-2.5-flash":
            raise Exception("404 Model Not Found or Quota Hit")
        elif model == "gemini-2.5-pro":
            c = MagicMock(text="Omniroute answered!", function_calls=None)
            return [c]
        raise Exception("Unknown model")

    mock_client.models.generate_content_stream.side_effect = mock_stream
    mock_client_cls.return_value = mock_client

    provider = GeminiProvider(api_key="AIzaSyDummyKey", model_name="gemini-2.5-flash", omniroute=True)
    events = list(provider.generate_response("Test prompt", stream=True))

    # Verify no error events were produced during the failover
    error_events = [e for e in events if e["type"] == "error"]
    assert len(error_events) == 0

    # Verify content chunk and complete event were yielded from fallback model
    chunks = [e["content"] for e in events if e["type"] == "chunk"]
    assert chunks == ["Omniroute answered!"]
    assert provider.active_model == "gemini-2.5-pro"
