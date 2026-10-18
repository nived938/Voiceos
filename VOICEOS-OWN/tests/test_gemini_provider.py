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
        if model == "gemini-3.8-flash":
            raise Exception("404 Model Not Found or Quota Hit")
        elif model == "gemini-3.6-flash":
            c = MagicMock(text="Omniroute answered!", function_calls=None)
            return [c]
        raise Exception("Unknown model")

    mock_client.models.generate_content_stream.side_effect = mock_stream
    mock_client_cls.return_value = mock_client

    provider = GeminiProvider(api_key="AIzaSyDummyKey", model_name="gemini-3.8-flash", omniroute=True)
    events = list(provider.generate_response("Test prompt", stream=True))

    # Verify no error events were produced during the failover
    error_events = [e for e in events if e["type"] == "error"]
    assert len(error_events) == 0

    # Verify content chunk and complete event were yielded from fallback model
    chunks = [e["content"] for e in events if e["type"] == "chunk"]
    assert chunks == ["Omniroute answered!"]
    assert provider.active_model == "gemini-3.6-flash"


@patch("google.genai.Client")
def test_gemini_dynamic_model_discovery(mock_client_cls):
    """
    Tests dynamic model discovery via client.models.list()
    """
    mock_client = MagicMock()
    m1 = MagicMock(name="models/gemini-3.8-flash")
    m1.name = "models/gemini-3.8-flash"
    m2 = MagicMock(name="models/gemini-custom-flash")
    m2.name = "models/gemini-custom-flash"
    mock_client.models.list.return_value = [m1, m2]
    mock_client_cls.return_value = mock_client

    provider = GeminiProvider(api_key="AIzaSyDummyKey", model_name="gemini-3.8-flash")
    discovered = provider.discover_models()
    assert "gemini-3.8-flash" in discovered
    assert "gemini-custom-flash" in discovered
    candidates = provider._get_candidate_models()
    assert "gemini-custom-flash" in candidates


@patch("google.genai.Client")
def test_gemini_failover_mid_stream_reset(mock_client_cls):
    """
    Tests that mid-stream interruption triggers a clean reset event to prevent
    duplicate or garbled response concatenation.
    """
    mock_client = MagicMock()

    class FailingStream:
        def __iter__(self):
            chunk1 = MagicMock(text="Partial text that broke...", function_calls=None)
            yield chunk1
            raise Exception("503 Service Unavailable / Stream dropped")

    def mock_stream(model, contents, config):
        if model == "gemini-3.8-flash":
            return FailingStream()
        elif model == "gemini-3.6-flash":
            return [MagicMock(text="Clean full response from fallback", function_calls=None)]
        raise Exception("Unknown model")

    mock_client.models.generate_content_stream.side_effect = mock_stream
    mock_client_cls.return_value = mock_client

    provider = GeminiProvider(api_key="AIzaSyDummyKey", model_name="gemini-3.8-flash", omniroute=True)
    events = list(provider.generate_response("Test prompt", stream=True))

    types = [e["type"] for e in events]
    assert "reset" in types
    chunks = [e["content"] for e in events if e["type"] == "chunk"]
    assert "Clean full response from fallback" in chunks

