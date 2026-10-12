# logic_manager.py

# Takes the AI's already-validated record (schema checks are in ai_manager.py) plus the user's restrictions, applies deterministic business rules and returns the final record.
# The AI is never the last word on safety: these rules can only RAISE risk, never lower it.
# Expects: risk_score, stall_knowledge, dietary_status (dict), allergy_conflicts, cross_contact_risks, ingredient_tree.
# Adds: "flags", a list of reasons whenever a rule changed or questioned the AI's verdict.

# Removes a child that just repeats its parent's name (e.g. Rice > Rice), keeping its verdict on the parent
def remove_repeated_children(node):
    if "children" not in node:
        return
    kept = []
    for child in node["children"]:
        if child["name"].strip().lower() == node["name"].strip().lower():
            if child["status"] == "Trigger":
                node["status"] = "Trigger"
                node["conflict"] = node["conflict"] or child["conflict"]
            # the repeated child may have its own children, so keep those
            kept.extend(child.get("children", []))
        else:
            kept.append(child)
    node["children"] = kept
    for child in node["children"]:
        remove_repeated_children(child)

# Walks the ingredient tree (children first), keeps parents consistent and collects every Trigger node
def collect_triggers(node, found, flags):
    # leaf nodes have no "children" key, so .get is used
    for child in node.get("children", []):
        collect_triggers(child, found, flags)

    child_triggered = any(child["status"] == "Trigger" for child in node.get("children", []))

    # A parent is a Trigger if anything below it is
    if child_triggered and node["status"] == "Safe":
        node["status"] = "Trigger"

    if node["status"] == "Trigger":
        # A Trigger needs a reason somewhere: its own, or one of its children's
        if not node["conflict"] and not child_triggered:
            node["conflict"] = "Flagged by the AI (no detail given)"
            flags.append(f"'{node['name']}' was marked Trigger without a reason.")
        found.append(node)
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

    data["flags"] = []
    user_restrictions = flatten_restrictions(restrictions)

    # Keep the score inside 0-100 in case the API goes out of range
    data["risk_score"] = max(0, min(100, data["risk_score"]))

    # The AI cannot verify certificates, so COMPLIANT is never accepted for them. This must also run before "uncertain" because it can add or change UNCERTAIN entries.
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

    # AI's own score, taken BEFORE any rule below raises it, so a clearly low rating is not bumped just because the AI listed a generic cross-contact note
    ai_noticed_risks = data["risk_score"] >= 10

    remove_repeated_children(data["ingredient_tree"])
    triggers = collect_triggers(data["ingredient_tree"], [], data["flags"])

    # A flagged ingredient that the stall's practice affects is worth telling the user about
    for node in triggers:
        if node.get("stall_insight"):
            data["flags"].append(f"Stall practice affects '{node['name']}': {node['stall_insight']}")

    # Multi-conditional check; Stall not really known AND user has restrictions AND shared-equipment risks AND AI also noticed risks, cannot stay in the Low band
    if has_restrictions and stall_unverified and len(data["cross_contact_risks"]) > 0 and ai_noticed_risks:
        raise_score(data, 30, "unverified stall with cross-contact risks.")

    # Conflicts or a NON-COMPLIANT status can never score below High
    if has_conflict or non_compliant:
        raise_score(data, 60, "the AI reported a conflict or non-compliant status.")

    # An UNCERTAIN status can never be less than Medium
    if uncertain:
        raise_score(data, 30, "a dietary requirement is UNCERTAIN.")

    # A Trigger ingredient in the tree can never score below Medium
    if triggers:
        raise_score(data, 30, "an ingredient is marked Trigger in the breakdown.")

    # Conflicts listed but nothing in the tree explains them: flag it, do not change the score
    if has_conflict and not triggers:
        data["flags"].append("Allergy conflicts were listed but no ingredient is marked Trigger. Verify with the vendor.")

    # The AI's own risk level counts too: never end up below what the AI said
    if data["risk_level"] == "High":
        raise_score(data, 60, "the AI rated the dish High risk.")

    elif data["risk_level"] == "Medium":
        raise_score(data, 30, "the AI rated the dish Medium risk.")

    # Low = 0-29 (safe), Medium = 30-59, High = 60-100 (Same as ai_manager.py scoring in prompt)
    if data["risk_score"] >= 60 :
        data["is_safe"] = False
        data["risk_level"] = "High"

    elif data["risk_score"] >= 30 :
        data["is_safe"] = False
        data["risk_level"] = "Medium"

    else:
        data["is_safe"] = True
        data["risk_level"] = "Low"

    return data