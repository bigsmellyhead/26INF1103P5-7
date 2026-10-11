# logic_manager.py

# Walks the ingredient tree and collects every node the AI marked as Trigger
def collect_triggers(node, found, flags):
    if node["status"] == "Trigger":
        # io_manager only prints red when a conflict exists, so a Trigger needs a reason
        if not node["conflict"] and not node.get("children"):
            node["conflict"] = "Flagged by the AI (no detail given)"
            flags.append(f"'{node['name']}' was marked Trigger without a reason.")
        found.append(node)

    # leaf nodes have no "children" key, so .get is used
    for child in node.get("children", []):
        collect_triggers(child, found, flags)
    return found

# Raises the score to a minimum (never lowers it) and records why
def raise_score(data, minimum, reason):
    if data["risk_score"] < minimum:
        data["risk_score"] = minimum
        data["flags"].append(f"Score raised to {minimum}: {reason}")

certification_requirements = ["halal", "kosher"]

# Flattens the grouped restrictions from io_manager into one plain list of items
def flatten_restrictions(restrictions):
    if isinstance(restrictions, dict):
        return [item for items in restrictions.values() for item in items]
    return [item for item in restrictions if item != "none"]

def validate_and_process_logic(data, restrictions):
    """
    Applies business rules to the AI result and decides the final outcome.
    Schema validation moved to ai_manager.py
    """

    data["flags"] = []
    user_restrictions = flatten_restrictions(restrictions)

    # Keep the score inside 0-100 in case the API goes out of range
    data["risk_score"] = max(0, min(100, data["risk_score"]))

    # The AI cannot verify certificates, so COMPLIANT is never accepted for them
    for requirement, status in list(data["dietary_status"].items()):
        if status == "COMPLIANT" and any(word in requirement.lower() for word in certification_requirements):
            data["dietary_status"][requirement] = "UNCERTAIN"
            data["flags"].append(f"{requirement} changed to UNCERTAIN: the AI cannot verify a certification.")

    # A certification requirement the user listed must always appear in dietary_status.
    # If the AI skipped it, mark it UNCERTAIN (we cannot verify a certificate)
    for item in user_restrictions:
        if item.lower() in certification_requirements:
            already_listed = any(item.lower() in name.lower() for name in data["dietary_status"])
            if not already_listed:
                data["dietary_status"][item.title()] = "UNCERTAIN"
                data["flags"].append(f"{item.title()} was not assessed by the AI, so it is marked UNCERTAIN.")
                
    has_conflict = len(data["allergy_conflicts"]) > 0
    non_compliant = "NON-COMPLIANT" in data["dietary_status"].values()
    uncertain = "UNCERTAIN" in data["dietary_status"].values()

    has_restrictions = len(user_restrictions) > 0
    stall_unverified = data["stall_knowledge"] in ["Inferred", "Unknown"]
    ai_noticed_risks = data["risk_score"] >= 10

    triggers = collect_triggers(data["ingredient_tree"], [], data["flags"])

    # Stall not really known AND user has restrictions AND shared-equipment risks: cannot stay in the Low band
    if has_restrictions and stall_unverified and len(data["cross_contact_risks"]) > 0 and ai_noticed_risks:
        raise_score(data, 30, "unverified stall with cross-contact risks.")

    # Conflicts or a NON-COMPLIANT status can never score below High
    if has_conflict or non_compliant:
        raise_score(data, 60, "the AI reported a conflict or non-compliant status.")

    # An UNCERTAIN status can never be less than Moderate
    if uncertain:
        raise_score(data, 30, "a dietary requirement is UNCERTAIN.")

    # A Trigger ingredient in the tree can never score below Medium
    if triggers:
        raise_score(data, 30, "an ingredient is marked Trigger in the breakdown.")

    # Conflicts listed but nothing in the tree explains them: flag it, do not change the score
    if has_conflict and not triggers:
        data["flags"].append("Allergy conflicts were listed but no ingredient is marked Trigger. Verify with the vendor.")

    # Deterministic safety rule override: >= 60% or High risk means unsafe
    # 30% -59% = Medium risk , 1%-29% = Lowrisk, < 1% = Negligible risk
    if data["risk_score"] >= 60 :
        data["is_safe"] = False
        data["risk_level"] = "High"
    elif data["risk_score"] >= 30 :
        data["is_safe"] = False
        data["risk_level"] = "Medium"
    # incase api gives risk score like 0.5 etc
    else:
        data["is_safe"] = True
        data["risk_level"] = "Low"

    return data