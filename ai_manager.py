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
    - "reasoning" : Short reason why it has the allergy
    - "hidden_ingredients" : list of hidden ingredients
    - "dietary_status": dictionary - Map each checked lifestyle/religious requirement to its compliance state (e.g., {{"Halal": "COMPLIANT", "Vegan": "COMPLIANT"}}). Strictly exclude allergies. If none, return an empty dictionary {{}}.
    - "allergy_conflicts": list of strings (e.g., ["Peanuts", "Tree Nuts (Cashews)"]) - Only list triggered violations; leave empty if none.
    - "ingredient_tree": object representing the dish hierarchy. 
      * CRITICAL RULE: Every node MUST have a "name" and a "status" ("Safe" or "Trigger"). 
      * Every node MUST include a "children" key containing a list (use an empty list [] if there are no sub-ingredients).
      * Do NOT repeat the main dish name inside child components (e.g., use "Oily Rice" or "Fragrant Rice", NOT "Chicken Rice (Oily Rice)").
      * If an item has a "Trigger" status, it MUST include a "conflict" field detailing the violation; otherwise, set "conflict" to null.
      * 
      Structure:
      {{
        "name": "string (Main Dish Name)",
        "status": "string (Safe / Unsafe)",
        "children": [
          {{
            "name": "string (Category or Ingredient Name)",
            "status": "string (Safe / Trigger)",
            "conflict": "string or []",
            "children": [
              {{
                "name": "string",
                "status": "string (Safe / Trigger)",
                "conflict": "string or null",
                "children": []
              }}
            ]
          }}
        ]
      }}
    """

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        ),
    )
    
    return response.text