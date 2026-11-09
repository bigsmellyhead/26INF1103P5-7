# logic_manager.py
from Data import Data, ValidateProcessData, AuditResultData
from EventName import EventName
from ingredient_tree_processor import IngredientTreeProcessor

# Takes the AI's already-validated record (schema checks are in ai_manager.py) plus the user's restrictions, applies deterministic business rules and raises the final record on the Bus.
# The AI is never the last word on safety: these rules can only RAISE risk, never lower it.
# Expects: risk_score, stall_knowledge, dietary_status (dict), allergy_conflicts, cross_contact_risks, ingredient_tree.
# Adds: "flags", a list of reasons whenever a rule changed or questioned the AI's verdict.


class LogicManager:

    def __init__(self, bus):
        self._bus = bus
        self._certification_requirements = ["halal", "kosher"]
        self._tree_processor = IngredientTreeProcessor()

        # Runs validate_and_process_logic whenever the AI result arrives
        self._bus.subscribe_event(EventName.VALIDATEPROCESSDATA, self.validate_and_process_logic)

    # Raises the score to a minimum (never lowers it) and records why
    def _raise_score(self, data: dict, minimum: int, reason: str) -> None:
        if data["risk_score"] < minimum:
            data["risk_score"] = minimum
            data["flags"].append(f"Score raised to {minimum}: {reason}")

    # Flattens the grouped restrictions from io_manager into one plain list of items
    def _flatten_restrictions(self, restrictions) -> list:
        if isinstance(restrictions, dict):
            return [item for items in restrictions.values() for item in items]
        return [item for item in restrictions if item != "none"]

    def validate_and_process_logic(self, event_data: Data) -> None:
        if not isinstance(event_data, ValidateProcessData):
            raise TypeError("LogicManager expects ValidateProcessData")

        data = event_data.ai_result
        restrictions = event_data.restrictions

        data["flags"] = []
        user_restrictions = self._flatten_restrictions(restrictions)

        # Keep the score inside 0-100 in case the API goes out of range
        data["risk_score"] = max(0, min(100, data["risk_score"]))

        # The AI cannot verify certificates, so COMPLIANT is never accepted for them. This must also run before "uncertain" because it can add or change UNCERTAIN entries.
        for requirement, status in list(data["dietary_status"].items()):
            if status == "COMPLIANT" and any(word in requirement.lower() for word in self._certification_requirements):
                data["dietary_status"][requirement] = "UNCERTAIN"
                data["flags"].append(f"{requirement} changed to UNCERTAIN: the AI cannot verify a certification.")

        # A certification requirement the user listed must always appear in dietary_status.
        # If the AI skipped it, mark it UNCERTAIN (we cannot verify a certificate)
        for item in user_restrictions:
            if item.lower() in self._certification_requirements:
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

        self._tree_processor.remove_repeated_children(data["ingredient_tree"])
        triggers = self._tree_processor.collect_triggers(data["ingredient_tree"], [], data["flags"])

        # A flagged ingredient that the stall's practice affects is worth telling the user about
        for node in triggers:
            if node.get("stall_insight"):
                data["flags"].append(f"Stall practice affects '{node['name']}': {node['stall_insight']}")

        # Multi-conditional check; Stall not really known AND user has restrictions AND shared-equipment risks AND AI also noticed risks, cannot stay in the Low band
        if has_restrictions and stall_unverified and len(data["cross_contact_risks"]) > 0 and ai_noticed_risks:
            self._raise_score(data, 30, "unverified stall with cross-contact risks.")

        # Conflicts or a NON-COMPLIANT status can never score below High
        if has_conflict or non_compliant:
            self._raise_score(data, 60, "the AI reported a conflict or non-compliant status.")

        # An UNCERTAIN status can never be less than Medium
        if uncertain:
            self._raise_score(data, 30, "a dietary requirement is UNCERTAIN.")

        # A Trigger ingredient in the tree can never score below Medium
        if triggers:
            self._raise_score(data, 30, "an ingredient is marked Trigger in the breakdown.")

        # Conflicts listed but nothing in the tree explains them: flag it, do not change the score
        if has_conflict and not triggers:
            data["flags"].append("Allergy conflicts were listed but no ingredient is marked Trigger. Verify with the vendor.")

        # The AI's own risk level counts too: never end up below what the AI said
        if data["risk_level"] == "High":
            self._raise_score(data, 60, "the AI rated the dish High risk.")

        elif data["risk_level"] == "Medium":
            self._raise_score(data, 30, "the AI rated the dish Medium risk.")

        # Low = 0-29 (safe), Medium = 30-59, High = 60-100 (Same as ai_manager.py scoring in prompt)
        if data["risk_score"] >= 60:
            data["is_safe"] = False
            data["risk_level"] = "High"

        elif data["risk_score"] >= 30:
            data["is_safe"] = False
            data["risk_level"] = "Medium"

        else:
            data["is_safe"] = True
            data["risk_level"] = "Low"

        # Hand the finished audit to whoever is listening (display, save)
        result = AuditResultData(
            event_data.username,
            event_data.stall,
            event_data.dish,
            restrictions,
            data,
        )
        self._bus.raise_event(EventName.AUDITRESULTDATA, result)
