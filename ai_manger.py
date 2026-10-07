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

# Halal , supper club 98 and carror cake are testing prompt, REMOVE after linking with io side
    prompt = f"""
    You are an expert food safety and dietary restriction auditor for Singapore eateries .
    Evaluate the following dish for a user with these dietary restrictions/allergies: (Halal)

    Hawker Centre/Stall:(Supper Club 98)
    Dish: (Carrot Cake)
    
    You MUST respond with a valid JSON object only (no markdown text blocks like ```json, just raw JSON string) containing exactly these keys:
    - "is_safe": boolean (true if completely safe, false otherwise)
    - "risk_score": number (0 to 100 integer representing risk percentage)
    - "stall_specific_insights": string (analysis of stall/hawker culture/hidden ingredients)
    - "hidden_ingredients": list of strings (potential unlisted ingredients or components)
    - "reasoning": string (short explanation of why it is safe or unsafe)
    """



    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        ),
    )

    print(response)

query_ai_safety_auditor()