# UserProfile.py
# The user's profile while the app is running.
# This file defines the format that the rest of the app sees
# Methods to read and update the profile are provided, but the rest of the app never sees the raw data.


class UserProfile:
    CATEGORIES = ("allergies", "dietary_restrictions", "other")

    def __init__(self, username: str, allergies=None, dietary_restrictions=None, other=None, severity=None):
        self._username = username
        self._restrictions = {}
        self._severity = {}
        self.set_restrictions(allergies or [], dietary_restrictions or [], other or [], severity or {})

    @property
    def username(self) -> str:
        return self._username

    # Get a copy of the list of restrictions in a category. Returns an empty list if the category is unknown.
    def items_in(self, category: str) -> list:
        return list(self._restrictions[category])

    # Get a list of all restrictions in all categories, in the order of CATEGORIES.
    def all_restriction_names(self) -> list:
        return [item for category in self.CATEGORIES for item in self._restrictions[category]]

    # find the restrictions that the user had return it and none if none
    def has_restrictions(self) -> bool:
        return len(self.all_restriction_names()) > 0

    # get a copy of the severity map {name: "LOW"/"MED"/"HIGH"}
    def severity_map(self) -> dict:
        return dict(self._severity)

    # get the severity label as text
    def severity_label(self, name: str):
        level = self.severity_of(name)
        return getattr(level, "value", level)

    # get the saved severity for one restriction 
    def severity_of(self, name: str):
        for saved_name, level in self._severity.items():
            if saved_name.lower() == name.strip().lower():
                return level
        return None

    # find restrictions that match a name from the AI. Exact match first; otherwise partial match (AI says "egg" -> chicken egg, duck egg, quail egg).
    def matching_restrictions(self, name: str) -> list:
        target = name.strip().lower() if isinstance(name, str) else ""
        if not target:
            return []

        names = self.all_restriction_names()
        exact = [n for n in names if n.lower() == target]
        if exact:
            return exact
        return [n for n in names if target in n.lower() or n.lower() in target]

    
    # Replace all restrictions. Severity for items no longer selected is dropped.
    def set_restrictions(self, allergies, dietary_restrictions, other, severity) -> None:
        self._restrictions = {
            "allergies": list(allergies),
            "dietary_restrictions": list(dietary_restrictions),
            "other": list(other),
        }
        current = {n.lower() for n in self.all_restriction_names()}
        self._severity = {
            name: level for name, level in severity.items() if name.lower() in current
        }

    def __repr__(self) -> str:
        return f"UserProfile({self._username!r}, {self._restrictions}, severity={self._severity})"
