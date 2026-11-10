# ai_manager.py
import json
import time
import logging

from io_manager import display_api_key_error, display_attempt_error
from output_schema import OutputSchema
from schema_validator import SchemaValidator
from prompt_builder import PromptBuilder
from gemini_client import GeminiClient

# Configue logging to save logs to api.logs, filemode 'a' to allow appending of new logs
# ERROR level are logged,in the format of date/time, level, message...
logging.basicConfig(filename="api.logs", filemode="a",level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

class AIManager:
    def __init__(self):
        # Stored here for easier model version change 
        self.model_name = "gemini-3.5-flash-lite"
        self.max_tries = 3
        self.ai_output_schema = OutputSchema.ai_output_schema

        #AI manager builds its helpers/classes (composition)
        self.client = GeminiClient(self.model_name)
        self.prompt_builder=PromptBuilder()
        self.validator=SchemaValidator()

    def _convert_dietary_status(self, data):
        # Transforms dietary status from a list-of-objects back into a dictionary map for the logic manager
        data["dietary_status"] = {item["requirement"]: item["status"] for item in data["dietary_status"]}
        return data
    
    def query_ai_safety_auditor(self,stall, dish, restrictions):

        #checks for api key
        if not self.client.has_api_key():
             #error will be logged to api.logs
            logging.error("GEMINI_API_KEY is not set")
            display_api_key_error()
            return None

        #calls build_user_message method to wraps sanitised user data in tags 
        user_data=self.prompt_builder.build_user_message(stall,dish,restrictions)

        for attempt in range(1, self.max_tries + 1):
            try:
                # calls for generate_reply method to get raw reply from api
                reply_text=self.client.generate_reply( user_data, self.prompt_builder.system_prompt(), self.ai_output_schema)
                data = json.loads(reply_text)

                # Validates the parsed JSON against the output schema, ensures that api did follow schema
                problems=self.validator.check_schema(data,self.ai_output_schema)
                if problems:
                    raise ValueError(f"Malformed response: {problems}")

                return self._convert_dietary_status(data)
            except Exception as error:
                #error will be logged to api.logs
                logging.error(f"Attempt {attempt}/{self.max_tries}:API has error: {error} ")
                display_attempt_error(attempt, self.max_tries, error)
                if attempt < self.max_tries:
                    time.sleep(2 * attempt)   # wait 2s after the 1st failure, 4s after the 2nd
                            
        return None
                

        
