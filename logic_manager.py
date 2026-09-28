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

    required_keys = ["is_safe", "risk_level", "risk_score", "stall_specific_insights", "hidden_ingredients", "reasoning"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Schema Validation Failed: Missing required key '{key}'")

    if not isinstance(data["is_safe"], bool):
        raise TypeError("Schema Validation Failed: 'is_safe' must be a boolean.")
    if not isinstance(data["risk_score"], (int, float)):
        raise TypeError("Schema Validation Failed: 'risk_score' must be a number.")

    return data