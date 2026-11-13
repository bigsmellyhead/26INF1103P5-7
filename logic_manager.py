# logic_manager.py
from Data import AIAuditData, ResultAuditData
from UserProfile import UserProfile
from ingredient_tree_processor import IngredientTreeProcessor
from severity_policy import SeverityPolicy
from severity_level import SeverityLevel

# Takes the AI's already-validated record (schema checks are in ai_manager.py) plus the user's profile,
# applies deterministic business rules and returns the final ResultAuditData.

# The AI is never the last word on safety. Rules RAISE the score, with ONE narrow, flagged exception:
# if every conflicting allergen is LOW severity (not life threatening), the dish is capped below High.

# Expects: risk_score, risk_level, stall_knowledge, dietary_status (dict), allergy_conflicts (list of {"restriction", "ingredient", "presence"}), cross_contact_risks, ingredient_tree.

# Adds: "flags" (reasons whenever a rule changed or questioned the AI) and "severity" on each conflict.


class LogicManager:

    def __init__(self):
        self._certification_requirements = ["halal", "kosher"]
        self._tree_processor = IngredientTreeProcessor()
        self._severity_policy = SeverityPolicy()

    # ---------- small score helpers ----------

    # Raises the score to a minimum (never lowers it) and records why
    def _raise_score(self, data: dict, minimum: int, reason: str) -> None:
        if data["risk_score"] < minimum:
            data["risk_score"] = minimum
            data["flags"].append(f"Score raised to {minimum}: {reason}")

    # Lowers the score to a maximum (only used by the LOW-severity rule) and records why
    def _cap_score(self, data: dict, maximum: int, reason: str) -> None:
        if data["risk_score"] > maximum:
            data["risk_score"] = maximum
            data["flags"].append(f"Score capped at {maximum}: {reason}")

    # ---------- rule groups ----------

    def _apply_certification_rules(self, data: dict, profile: UserProfile) -> None:
        # The AI cannot verify certificates, so COMPLIANT is never accepted for them.
        for requirement, status in list(data["dietary_status"].items()):
            if status == "COMPLIANT" and any(word in requirement.lower() for word in self._certification_requirements):
                data["dietary_status"][requirement] = "UNCERTAIN"
                data["flags"].append(f"{requirement} changed to UNCERTAIN: the AI cannot verify a certification.")

        # A certification requirement the user listed must always appear in dietary_status
        for item in profile.all_restriction_names():
            if item.lower() in self._certification_requirements:
                already_listed = any(item.lower() in name.lower() for name in data["dietary_status"])
                if not already_listed:
                    data["dietary_status"][item.title()] = "UNCERTAIN"
                    data["flags"].append(f"{item.title()} was not assessed by the AI, so it is marked UNCERTAIN.")

    # Look up the USER's severity for the restriction the AI named. The AI never decides the severity.
    def _conflict_severity(self, conflict: dict, profile: UserProfile, flags: list) -> SeverityLevel:
        named = conflict.get("restriction", "")
        matches = profile.matching_restrictions(named)

        if not matches:
            worst = self._severity_policy.most_severe([])   # DEFAULT_SEVERITY (HIGH)
            flags.append(f"The AI linked a conflict to '{named}', which is not in the profile. Treated as {worst.value} severity.")
            return worst

        # If the name matches several items (e.g. "egg"), the most severe one counts
        return self._severity_policy.most_severe([profile.severity_of(name) for name in matches])

    # Raise the score per conflict using severity x presence. Returns the severities found.
    def _apply_severity_rules(self, data: dict, profile: UserProfile) -> list:   
        severities = []
        for conflict in data["allergy_conflicts"]:
            severity = self._conflict_severity(conflict, profile, data["flags"])
            presence = self._severity_policy.normalise_presence(conflict.get("presence"))

            # Store as plain text on the conflict so the report can show it and MySQL can save it as JSON
            conflict["severity"] = severity.value
            conflict["presence"] = presence
            severities.append(severity)

            floor = self._severity_policy.floor_for(severity, presence)
            self._raise_score(data, floor, f"{severity.value}-severity '{conflict.get('restriction')}' is {presence.lower()} in the dish.")
        return severities

    def _apply_risk_band(self, data: dict) -> None:
        # Low = 0-29 (safe), Medium = 30-59, High = 60-100 (same as the prompt)
        if data["risk_score"] >= 60:
            data["is_safe"], data["risk_level"] = False, "High"
        elif data["risk_score"] >= 30:
            data["is_safe"], data["risk_level"] = False, "Medium"
        else:
            data["is_safe"], data["risk_level"] = True, "Low"

    # ---------- main entry point ----------

    def validate_and_process_logic(self, ai_data: AIAuditData) -> ResultAuditData:
        if not isinstance(ai_data, AIAuditData):
            raise TypeError("LogicManager expects AIAuditData")

        data = ai_data.ai_result
        profile = ai_data.user_profile
        data["flags"] = []

        # Keep the score inside 0-100 in case the API goes out of range
        data["risk_score"] = max(0, min(100, data["risk_score"]))

        # Must run before "uncertain" is computed, because it can add UNCERTAIN entries
        self._apply_certification_rules(data, profile)

        has_conflict = len(data["allergy_conflicts"]) > 0
        non_compliant = "NON-COMPLIANT" in data["dietary_status"].values()
        uncertain = "UNCERTAIN" in data["dietary_status"].values()
        stall_unverified = data["stall_knowledge"] in ["Inferred", "Unknown"]

        # AI's own score, taken BEFORE any rule raises it
        ai_noticed_risks = data["risk_score"] >= 10

        self._tree_processor.remove_repeated_children(data["ingredient_tree"])
        triggers = self._tree_processor.collect_triggers(data["ingredient_tree"], [], data["flags"])

        for node in triggers:
            if node.get("stall_insight"):
                data["flags"].append(f"Stall practice affects '{node['name']}': {node['stall_insight']}")

        # 1. Severity-based floor for every allergy conflict
        severities = self._apply_severity_rules(data, profile)

        # 2. Unverified stall + restrictions + shared equipment + AI saw risk -> not Low
        if profile.has_restrictions() and stall_unverified and len(data["cross_contact_risks"]) > 0 and ai_noticed_risks:
            self._raise_score(data, 30, "unverified stall with cross-contact risks.")

        # 3. Dietary rules have no severity: NON-COMPLIANT is always High, UNCERTAIN at least Medium
        if non_compliant:
            self._raise_score(data, 60, "a dietary requirement is NON-COMPLIANT.")
        if uncertain:
            self._raise_score(data, 30, "a dietary requirement is UNCERTAIN.")

        # 4. Trigger ingredients in the tree. When conflicts exist, step 1 already scored them by severity, so a Trigger only adds a rule when the AI did NOT say which allergen it is.
        if has_conflict and not triggers:
            data["flags"].append("Allergy conflicts were listed but no ingredient is marked Trigger. Verify with the vendor.")

        if triggers and not has_conflict:
            rated = profile.severity_map()
            if rated:
                # We don't know WHICH allergen the trigger is, so assume the user's worst one (fail-safe)
                worst = self._severity_policy.most_severe(rated.values())
                self._raise_score(data, self._severity_policy.floor_for(worst, SeverityPolicy.POSSIBLE),
                                  f"a Trigger ingredient has no matching conflict, so your most severe level ({worst.value}) is assumed.")
            else:
                # Only dietary requirements (no severity)
                self._raise_score(data, 30, "an ingredient is marked Trigger in the breakdown.")

        # 5. Never end up below what the AI itself said
        if data["risk_level"] == "High":
            self._raise_score(data, 60, "the AI rated the dish High risk.")
        elif data["risk_level"] == "Medium":
            self._raise_score(data, 30, "the AI rated the dish Medium risk.")

        # 6. The one exception: only LOW-severity allergens involved and no dietary breach -> not High
        only_mild = has_conflict and all(s == SeverityLevel.LOW for s in severities) and not non_compliant
        if only_mild:
            self._cap_score(data, SeverityPolicy.MILD_ONLY_CAP,
                            "every conflicting allergen is LOW severity (not life-threatening).")

        self._apply_risk_band(data)

        return ResultAuditData(ai_data.user_profile, ai_data.stall, ai_data.dish, data)
