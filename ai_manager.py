# ai_manager.py
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv 

#This is so that we do not have to keep putting our own API key into the terminal
load_dotenv()                  

def query_ai_safety_auditor(stall, dish, restrictions_list):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please set it in your .env file.")

    client = genai.Client(api_key=api_key)
    
    restrictions_str = ", ".join(restrictions_list)
    
    prompt = f"""
    You are an expert food safety and dietary restriction auditor for Singapore hawker centres.
    Evaluate the following dish for a user with these dietary restrictions/allergies: [{restrictions_str}].
    
    Hawker Centre/Stall: {stall}
    Dish: {dish}
    
    You MUST respond with a valid JSON object only (no markdown text blocks like ```json, just raw JSON string) containing exactly these keys:
    - "is_safe": boolean (true if completely safe, false otherwise)
    - "risk_level": string ("Low", "Medium", or "High")
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
    
    return response.text