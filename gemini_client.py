import os
from google import genai
from google.genai import types
from dotenv import load_dotenv 

# This is so that we do not have to keep putting our own API key into the terminal
load_dotenv()  

class GeminiClient:
    def __init__(self, model_name):
        self.model_name=model_name
        self.api_key= os.environ.get("GEMINI_API_KEY")
        self.client =genai.Client(api_key=self.api_key) if self.api_key else None #creates client only if key is present, return None if it is not


    #checks if api key is present
    def has_api_key(self):
        return True if self.api_key else False

    #passes schema ,user data and prompt to api
    #gets reply for api 
    def generate_reply(self, user_data, ai_prompt, ai_output_schema):
        response = self.client.models.generate_content(
            model=self.model_name,
            contents =user_data,
            config=types.GenerateContentConfig(
                system_instruction=ai_prompt,
                response_mime_type="application/json",
                response_schema=ai_output_schema,  #requires api to follow the output schema structure 
                temperature=0,
                top_k=1,
                seed=42,
            ),
        )
        return response.text
    

        