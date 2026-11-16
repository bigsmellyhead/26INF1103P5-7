
import json
import logging
from unittest.mock import Mock

import ai_manager as am


class TestAIManager:

    def setup_method(self):
        self.print_error = Mock()
        self.manager = am.AIManager(self.print_error)

    def mock_dependencies(self, monkeypatch, api_key=True,
                           reply=None, side_effect=None,
                           validation_problems=None):
        client = Mock()
        client.has_api_key.return_value = api_key

        if side_effect is not None:
            client.generate_reply.side_effect = side_effect
        else:
            client.generate_reply.return_value = (
                reply if reply is not None else json.dumps({
                    "dietary_status": [
                        {
                            "requirement": "Vegetarian",
                            "status": "COMPLIANT"
                        }
                    ]
                })
            )

        prompt_builder = Mock()
        prompt_builder.build_user_message.return_value = "Test user data"
        prompt_builder.system_prompt.return_value = "Test system prompt"

        validator = Mock()
        validator.check_schema.return_value = (
            validation_problems if validation_problems is not None else []
        )

        monkeypatch.setattr(am, "GeminiClient", lambda model: client)
        monkeypatch.setattr(am, "PromptBuilder", lambda: prompt_builder)
        monkeypatch.setattr(am, "SchemaValidator", lambda: validator)

        self.manager = am.AIManager(self.print_error)

        return client, prompt_builder, validator

    def test_initialization(self):
        assert self.manager._model_name == "gemini-3.5-flash-lite"
        assert self.manager._max_tries == 3
        assert self.manager._client is not None
        assert self.manager._prompt_builder is not None
        assert self.manager._validator is not None

    def test_missing_api_key(self, monkeypatch):
        client, _, _ = self.mock_dependencies(
            monkeypatch,
            api_key=False
        )

        result = self.manager.query_ai_safety_auditor(
            "Stall A", "Chicken Rice", {}
        )

        assert result is None
        client.generate_reply.assert_not_called()
        self.print_error.assert_called_once()

    def test_successful_response(self, monkeypatch):
        reply = {
            "dietary_status": [
                {
                    "requirement": "Vegetarian",
                    "status": "COMPLIANT"
                }
            ]
        }

        client, _, _ = self.mock_dependencies(
            monkeypatch,
            reply=json.dumps(reply)
        )

        result = self.manager.query_ai_safety_auditor(
            "Stall A", "Chicken Rice", {}
        )

        assert result == {
            "dietary_status": {
                "Vegetarian": "COMPLIANT"
            }
        }
        client.generate_reply.assert_called_once()

    def test_prompt_builder_receives_inputs(self, monkeypatch):
        _, prompt_builder, _ = self.mock_dependencies(monkeypatch)

        self.manager.query_ai_safety_auditor(
            "Stall A", "Chicken Rice", {"test": "profile"}
        )

        prompt_builder.build_user_message.assert_called_once_with(
            "Stall A", "Chicken Rice", {"test": "profile"}
        )

    def test_system_prompt_and_schema_are_sent(self, monkeypatch):
        client, prompt_builder, _ = self.mock_dependencies(monkeypatch)

        self.manager.query_ai_safety_auditor(
            "Stall A", "Chicken Rice", {}
        )

        args = client.generate_reply.call_args

        assert args.args[0] == "Test user data"
        assert args.args[1] == "Test system prompt"
        assert args.args[2] is am.OutputSchema.ai_output_schema

    def test_invalid_json_is_retried(self, monkeypatch):
        client, _, _ = self.mock_dependencies(
            monkeypatch,
            side_effect=[
                "not valid JSON",
                json.dumps({"dietary_status": []})
            ]
        )

        monkeypatch.setattr(am.time, "sleep", Mock())

        result = self.manager.query_ai_safety_auditor(
            "Stall A", "Chicken Rice", {}
        )

        assert result == {"dietary_status": {}}
        assert client.generate_reply.call_count == 2

    def test_invalid_schema_is_retried(self, monkeypatch):
        client, _, validator = self.mock_dependencies(monkeypatch)

        validator.check_schema.side_effect = [
            ["reply has the wrong type"],
            []
        ]

        monkeypatch.setattr(am.time, "sleep", Mock())

        result = self.manager.query_ai_safety_auditor(
            "Stall A", "Chicken Rice", {}
        )

        assert result == {
            "dietary_status": {
                "Vegetarian": "COMPLIANT"
            }
        }
        assert client.generate_reply.call_count == 2

    def test_api_exception_is_retried(self, monkeypatch):
        client, _, _ = self.mock_dependencies(
            monkeypatch,
            side_effect=[
                Exception("API unavailable"),
                json.dumps({"dietary_status": []})
            ]
        )

        monkeypatch.setattr(am.time, "sleep", Mock())

        result = self.manager.query_ai_safety_auditor(
            "Stall A", "Chicken Rice", {}
        )

        assert result == {"dietary_status": {}}
        assert client.generate_reply.call_count == 2

    def test_exhausted_retries_returns_none(self, monkeypatch):
        client, _, _ = self.mock_dependencies(
            monkeypatch,
            side_effect=Exception("API unavailable")
        )

        monkeypatch.setattr(am.time, "sleep", Mock())

        result = self.manager.query_ai_safety_auditor(
            "Stall A", "Chicken Rice", {}
        )

        assert result is None
        assert client.generate_reply.call_count == 3
        assert self.print_error.call_count == 3

    def test_retry_delay(self, monkeypatch):
        self.mock_dependencies(
            monkeypatch,
            side_effect=Exception("API unavailable")
        )

        sleep_mock = Mock()
        monkeypatch.setattr(am.time, "sleep", sleep_mock)

        self.manager.query_ai_safety_auditor(
            "Stall A", "Chicken Rice", {}
        )

        assert sleep_mock.call_count == 2
        assert [call.args[0] for call in sleep_mock.call_args_list] == [2, 4]

    def test_dietary_status_conversion(self):
        data = {
            "dietary_status": [
                {
                    "requirement": "Vegetarian",
                    "status": "COMPLIANT"
                },
                {
                    "requirement": "Halal",
                    "status": "UNCERTAIN"
                }
            ]
        }

        result = self.manager._convert_dietary_status(data)

        assert result["dietary_status"] == {
            "Vegetarian": "COMPLIANT",
            "Halal": "UNCERTAIN"
        }
