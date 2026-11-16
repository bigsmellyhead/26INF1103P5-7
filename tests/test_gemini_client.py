
import os
from unittest.mock import Mock

import gemini_client as gc


class TestGeminiClient:

    def setup_method(self):
        self.model_name = "gemini-3.5-flash-lite"

    def test_initialization_with_api_key(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")

        mock_client = Mock()
        client_factory = Mock(return_value=mock_client)

        monkeypatch.setattr(gc.genai, "Client", client_factory)

        client = gc.GeminiClient(self.model_name)

        assert client.model_name == self.model_name
        assert client.api_key == "test-api-key"
        assert client.client is mock_client
        client_factory.assert_called_once_with(
            api_key="test-api-key"
        )

    def test_initialization_without_api_key(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

        client_factory = Mock()
        monkeypatch.setattr(gc.genai, "Client", client_factory)

        client = gc.GeminiClient(self.model_name)

        assert client.api_key is None
        assert client.client is None
        client_factory.assert_not_called()

    def test_has_api_key_returns_true(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")
        monkeypatch.setattr(gc.genai, "Client", Mock())

        client = gc.GeminiClient(self.model_name)

        assert client.has_api_key() is True

    def test_has_api_key_returns_false(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

        client = gc.GeminiClient(self.model_name)

        assert client.has_api_key() is False

    def test_generate_reply_returns_response_text(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")

        mock_response = Mock()
        mock_response.text = '{"risk_score": 20}'

        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response

        monkeypatch.setattr(
            gc.genai,
            "Client",
            Mock(return_value=mock_client)
        )

        mock_config = Mock()
        config_factory = Mock(return_value=mock_config)

        monkeypatch.setattr(
            gc.types,
            "GenerateContentConfig",
            config_factory
        )

        client = gc.GeminiClient(self.model_name)

        result = client.generate_reply(
            "Test user data",
            "Test system prompt",
            {"type": "OBJECT"}
        )

        assert result == '{"risk_score": 20}'

        mock_client.models.generate_content.assert_called_once()

        call_kwargs = (
            mock_client.models.generate_content.call_args.kwargs
        )

        assert call_kwargs["model"] == self.model_name
        assert call_kwargs["contents"] == "Test user data"
        assert call_kwargs["config"] is mock_config

        config_kwargs = config_factory.call_args.kwargs

        assert config_kwargs["system_instruction"] == "Test system prompt"
        assert config_kwargs["response_mime_type"] == "application/json"
        assert config_kwargs["response_schema"] == {"type": "OBJECT"}
        assert config_kwargs["temperature"] == 0
        assert config_kwargs["top_k"] == 1
        assert config_kwargs["seed"] == 42

    def test_generate_reply_propagates_api_exception(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")

        mock_client = Mock()
        mock_client.models.generate_content.side_effect = Exception(
            "Gemini API error"
        )

        monkeypatch.setattr(
            gc.genai,
            "Client",
            Mock(return_value=mock_client)
        )

        monkeypatch.setattr(
            gc.types,
            "GenerateContentConfig",
            Mock()
        )

        client = gc.GeminiClient(self.model_name)

        try:
            client.generate_reply(
                "Test user data",
                "Test system prompt",
                {"type": "OBJECT"}
            )
            assert False, "Expected an exception"
        except Exception as error:
            assert str(error) == "Gemini API error"
