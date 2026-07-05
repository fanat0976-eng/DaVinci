"""Tests for LLM client."""

import json
from unittest.mock import patch, MagicMock

from davinci.llm.client import LLMClient


def test_client_defaults():
    """Client has correct defaults."""
    client = LLMClient()
    assert client.base_url == "http://127.0.0.1:11434"
    assert client.model == "qwen2.5:14b"
    assert client.timeout == 120


def test_client_custom():
    """Client accepts custom params."""
    client = LLMClient(base_url="http://localhost:8080", model="gpt-4", timeout=60)
    assert client.base_url == "http://localhost:8080"
    assert client.model == "gpt-4"
    assert client.timeout == 60


def test_client_strips_trailing_slash():
    """Client strips trailing slash from base_url."""
    client = LLMClient(base_url="http://localhost:11434/")
    assert client.base_url == "http://localhost:11434"


@patch("davinci.llm.client.requests.post")
def test_chat_success(mock_post):
    """Chat returns message content."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"message": {"content": "Hello!"}}
    mock_resp.raise_for_status = MagicMock()
    mock_post.return_value = mock_resp

    client = LLMClient()
    result = client.chat([{"role": "user", "content": "Hi"}])
    assert result == "Hello!"
    mock_post.assert_called_once()


@patch("davinci.llm.client.requests.post")
def test_chat_payload(mock_post):
    """Chat sends correct payload."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"message": {"content": "ok"}}
    mock_resp.raise_for_status = MagicMock()
    mock_post.return_value = mock_resp

    client = LLMClient(model="test-model")
    client.chat([{"role": "user", "content": "test"}], temperature=0.5, max_tokens=100)

    call_kwargs = mock_post.call_args
    payload = call_kwargs[1]["json"]
    assert payload["model"] == "test-model"
    assert payload["options"]["temperature"] == 0.5
    assert payload["options"]["num_predict"] == 100
    assert payload["stream"] is False


@patch("davinci.llm.client.requests.post")
def test_chat_stream(mock_post):
    """Chat stream yields tokens."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()

    # Simulate streaming response
    lines = [
        json.dumps({"message": {"content": "Hello"}, "done": False}).encode(),
        json.dumps({"message": {"content": " World"}, "done": False}).encode(),
        json.dumps({"done": True}).encode(),
    ]
    mock_resp.iter_lines.return_value = lines
    mock_post.return_value = mock_resp

    client = LLMClient()
    tokens = list(client.chat_stream([{"role": "user", "content": "Hi"}]))
    assert tokens == ["Hello", " World"]


@patch("davinci.llm.client.requests.get")
def test_is_available_true(mock_get):
    """is_available returns True when model exists."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"models": [{"name": "qwen2.5:14b"}]}
    mock_get.return_value = mock_resp

    client = LLMClient(model="qwen2.5:14b")
    assert client.is_available() is True


@patch("davinci.llm.client.requests.get")
def test_is_available_false(mock_get):
    """is_available returns False when model missing."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"models": [{"name": "other-model"}]}
    mock_get.return_value = mock_resp

    client = LLMClient(model="qwen2.5:14b")
    assert client.is_available() is False


@patch("davinci.llm.client.requests.get")
def test_is_available_error(mock_get):
    """is_available returns False on error."""
    mock_get.side_effect = Exception("Connection refused")
    client = LLMClient()
    assert client.is_available() is False
