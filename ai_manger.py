import os
from google import genai
from google.genai import types
from dotenv import load_dotenv 

#
load_dotenv()


def query_ai_safety_auditor():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please set it in your .env file.")

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents="this is a test pls reply with hello world",
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        ),
    )
    #for testing purposes, DELETE AFT linking with other files 
    print(response)


#for testing purposes, DELETE AFT linking with other files 
query_ai_safety_auditor()