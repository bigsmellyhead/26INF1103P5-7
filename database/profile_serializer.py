# profile_serializer.py
# The ONLY place that knows the shape of the "restrictions" JSON column:
# {"allergies": [...], "dietary_restrictions": [...], "other": [...], "severity": {name: LEVEL}}
#
#   deserialize: database dict  -> UserProfile object   (when loading)
#   serialize:   UserProfile    -> database dict        (only when saving)

from models.UserProfile import UserProfile
from logic.severity_policy import SeverityPolicy


class ProfileSerializer:

    def deserialize(self, username: str, restrictions) -> UserProfile:
        """Build a UserProfile from what MySQL gave us. Cleans up bad / old data."""
        if not isinstance(restrictions, dict):
            restrictions = {}

        lists = {category: self._clean_list(restrictions.get(category))
                 for category in UserProfile.CATEGORIES}

        return UserProfile(
            username,
            lists["allergies"],
            lists["dietary_restrictions"],
            lists["other"],
            self._clean_severity(restrictions.get("severity")),
        )

    def serialize(self, profile: UserProfile) -> dict:
        """Turn the profile back into the dict stored in the restrictions column."""
        data = {category: profile.items_in(category) for category in UserProfile.CATEGORIES}
        data["severity"] = profile.severity_map()
        return data

    # ---------- private helpers ----------

    def _clean_list(self, value) -> list:
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, (list, tuple)):
            return []
        return [item.strip() for item in value if isinstance(item, str) and item.strip() and item != "none"]

    def _clean_severity(self, value) -> dict:
        """Keep only valid levels. Unknown levels are dropped, so the logic treats them as HIGH."""
        if not isinstance(value, dict):
            return {}

        cleaned = {}
        for name, level in value.items():
            if not isinstance(name, str) or not isinstance(level, str):
                continue
            name = name.strip()
            level = level.strip().upper()
            level = "MED" if level == "MEDIUM" else level

            if name and SeverityPolicy.is_valid_level(level):
                cleaned[name] = level
        return cleaned
