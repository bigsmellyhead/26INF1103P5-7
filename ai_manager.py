# ai_manager.py
import json
import time
import logging

from output_schema import OutputSchema
from schema_validator import SchemaValidator
from prompt_builder import PromptBuilder
from gemini_client import GeminiClient
from collections.abc import Callable

class AIManager:
    __print_error: Callable

    def __init__(self, print_error: Callable):
        self.__print_error = print_error


        # Configure logging to save logs to api.logs, filemode 'a' to allow appending of new logs
        # ERROR level are logged, in the format of date/time, level, message...
        logging.basicConfig(filename="api.logs", filemode="a", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

        # Stored here for easier model version change
        self._model_name = "gemini-3.5-flash-lite"
        self._max_tries = 3
        self._ai_output_schema = OutputSchema.ai_output_schema

        # AI manager builds its helpers/classes (composition)
        self._client = GeminiClient(self._model_name)
        self._prompt_builder = PromptBuilder()
        self._validator = SchemaValidator()

    def _convert_dietary_status(self, data):
        # Transforms dietary status from a list-of-objects back into a dictionary map for the logic manager
        data["dietary_status"] = {item["requirement"]: item["status"] for item in data["dietary_status"]}
        return data

    def query_ai_safety_auditor(self, stall, dish, profile):

        # checks for api key
        if not self._client.has_api_key():
            # error will be logged to api.logs
            logging.error("GEMINI_API_KEY is not set")
            self.__print_error("[AI Manager] GEMINI_API_KEY is not set. Please set it in your .env file.")
            return None

        # calls build_user_message method to wrap sanitised user data in tags
        user_data = self._prompt_builder.build_user_message(stall, dish, profile)

        for attempt in range(1, self._max_tries + 1):
            try:
                # calls generate_reply method to get raw reply from api
                reply_text = self._client.generate_reply(user_data, self._prompt_builder.system_prompt(), self._ai_output_schema)
                data = json.loads(reply_text)

                # Validates the parsed JSON against the output schema, ensures that api did follow schema
                problems = self._validator.check_schema(data, self._ai_output_schema)
                if problems:
                    raise ValueError(f"Malformed response: {problems}")

                return self._convert_dietary_status(data)
            except Exception as error:
                # error will be logged to api.logs
                logging.error(f"Attempt {attempt}/{self._max_tries}:API has error: {error} ")
            # Calls IO manager display_error (passed in as print_error) to show the message
                error_msg = f"[AI Manager] Attempt {attempt}/{self._max_tries} failed: {error}"
                self.__print_error(error_msg)
                if attempt < self._max_tries:
                    time.sleep(2 * attempt)   # wait 2s after the 1st failure, 4s after the 2nd
                

        return None
