# profile_serializer.py
# This is the only file that has any conversion from data to UserProfile objects. The rest of the code never sees raw data.
# {"allergies": [...], "dietary_restrictions": [...], "other": [...], "severity": {name: LEVEL}}
#
#   deserialize : database dict  -> UserProfile object   (when loading)
#   serialize   : UserProfile    -> database dict        (only when saving)

from UserProfile import UserProfile
from severity_policy import SeverityPolicy


class ProfileSerializer:

    # Builds the UserProfile from the raaw data and cleans up bad and old data. Returns a UserProfile object.
    def deserialize(self, username: str, restrictions) -> UserProfile:
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

    
    # "Serialize" the UserProfile back into the dict stored in the database. The rest of the code never sees this.
    def serialize(self, profile: UserProfile) -> dict:
        data = {category: profile.items_in(category) for category in UserProfile.CATEGORIES}
        data["severity"] = profile.severity_map()
        return data

    
    # Clean up a list of restrictions. Remove empty strings, None, and "none". Strip whitespace. Return a list of strings.
    def _clean_list(self, value) -> list:
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, (list, tuple)):
            return []
        return [item.strip() for item in value if isinstance(item, str) and item.strip() and item != "none"]

    # Clean up the severity map. Keep only valid levels. Unknown levels are dropped, so the logic treats them as HIGH.
    def _clean_severity(self, value) -> dict:
        if not isinstance(value, dict):
            return {}

        cleaned = {}
        for name, level in value.items():
            if not isinstance(name, str) or not isinstance(level, str):
                continue
            level = level.strip().upper()
            level = "MED" if level == "MEDIUM" else level
            if level in SeverityPolicy.LEVELS:
                cleaned[name.strip()] = level
        return cleaned
