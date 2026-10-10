# logic_manager.py
import json

def validate_and_process_logic(raw_ai_response):
    """
    Validates AI schema, checks data types, and applies deterministic safety overrides.
    """
    try:
        data = json.loads(raw_ai_response)
    except json.JSONDecodeError:
        raise ValueError("Error: AI response is not valid JSON format.")

    required_keys = ["risk_score", "stall_specific_insights", "hidden_ingredients", "reasoning"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Schema Validation Failed: Missing required key '{key}'")

    if not isinstance(data["risk_score"], (int, float)):
        raise TypeError("Schema Validation Failed: 'risk_score' must be a number.")

    # Deterministic safety rule override: >= 60% or High risk means unsafe
    #30% -59% = Moderate risk , 1%-29% = Lowrisk, < 1% = Negligible risk
    if data["risk_score"] >= 60 :
        data["is_safe"] = False
        data["risk_level"] = "High"
    elif data["risk_score"] >= 30 :
        data["is_safe"] = False
        data["risk_level"] = "Moderate"
    # incase api gives risk score like 0.5 etc
    elif data["risk_score"] >0:
        data["is_safe"] = False
        data["risk_level"] = "Low"
    else:
        data["is_safe"] = True
        data["risk_level"] = "Negligible"


    return data