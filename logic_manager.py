# logic_manager.py

# Raises the score to a minimum (never lowers it) and records why
def raise_score(data, minimum, reason):
    if data["risk_score"] < minimum:
        data["risk_score"] = minimum
        data["flags"].append(f"Score raised to {minimum}: {reason}")

def validate_and_process_logic(data):
    """
    Applies business rules to the AI result and decides the final outcome.
    Schema validation moved to ai_manager.py
    """

    data["flags"] = []

    # Keep the score inside 0-100 in case the API goes out of range
    data["risk_score"] = max(0, min(100, data["risk_score"]))

    has_conflict = len(data["allergy_conflicts"]) > 0
    non_compliant = "NON-COMPLIANT" in data["dietary_status"].values()
    uncertain = "UNCERTAIN" in data["dietary_status"].values()

    # Conflicts or a NON-COMPLIANT status can never score below High
    if has_conflict or non_compliant:
        raise_score(data, 60, "the AI reported a conflict or non-compliant status.")

    # An UNCERTAIN status can never be less than Moderate
    if uncertain:
        raise_score(data, 30, "a dietary requirement is UNCERTAIN.")

    # Deterministic safety rule override: >= 60% or High risk means unsafe
    # 30% -59% = Moderate risk , 1%-29% = Lowrisk, < 1% = Negligible risk
    if data["risk_score"] >= 60 :
        data["is_safe"] = False
        data["risk_level"] = "High"
    elif data["risk_score"] >= 30 :
        data["is_safe"] = False
        data["risk_level"] = "Medium"
    # incase api gives risk score like 0.5 etc
    elif data["risk_score"] >0:
        data["is_safe"] = False
        data["risk_level"] = "Low"
    else:
        data["is_safe"] = True
        data["risk_level"] = "Negligible"

    return data