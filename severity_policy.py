# severity_policy.py

from severity_level import SeverityLevel
from allergen_catalog import DEFAULT_SEVERITY


class SeverityPolicy:
    # How sure the AI is that the allergen is in the dish / This must match the enum in output_schema.py
    CONFIRMED = "CONFIRMED"   # a standard / listed ingredient
    POSSIBLE = "POSSIBLE"     # hidden ingredient, sauce, or shared equipment / cross-contact
    PRESENCES = (CONFIRMED, POSSIBLE)

    # Minimum risk score for one allergy conflict, by (severity, presence).
    # Low = 0-29, Medium = 30-59, High = 60-100 (same bands as the prompt).
    # Class body order matters: CONFIRMED/POSSIBLE must be defined above this table.
    _FLOORS = {
        (SeverityLevel.HIGH, CONFIRMED): 80,   # life-threatening and definitely in the dish
        (SeverityLevel.HIGH, POSSIBLE): 60,    # life-threatening: even traces are High
        (SeverityLevel.MED, CONFIRMED): 45,
        (SeverityLevel.MED, POSSIBLE): 30,
        (SeverityLevel.LOW, CONFIRMED): 30,    # mild, but it IS in the dish -> still not "safe"
        (SeverityLevel.LOW, POSSIBLE): 10,     # mild and only maybe -> stays Low, but flagged
    }

    # If EVERY conflicting allergen is LOW severity, the dish cannot end up High
    MILD_ONLY_CAP = 59

    _RANK = {SeverityLevel.LOW: 1, SeverityLevel.MED: 2, SeverityLevel.HIGH: 3}

    def normalise(self, level) -> SeverityLevel:
        # If the SeverityLevel is not recognised/missing/unknown, the default severity is HIGH
        if isinstance(level, SeverityLevel):
            return level
        if isinstance(level, str):
            text = level.strip().upper()
            text = "MED" if text == "MEDIUM" else text
            try:
                return SeverityLevel(text)
            except ValueError:
                pass
        return DEFAULT_SEVERITY

    def normalise_presence(self, presence) -> str:
        # Unknown presence is treated as CONFIRMED - as per our business rules
        if isinstance(presence, str) and presence.strip().upper() in self.PRESENCES:
            return presence.strip().upper()
        return self.CONFIRMED

    def most_severe(self, levels) -> SeverityLevel:
        # If list is empty or severity was not specified for the allergen - HIGH is the default severity 
        cleaned = [self.normalise(level) for level in levels]
        if not cleaned:
            return DEFAULT_SEVERITY
        return max(cleaned, key=lambda level: self._RANK[level])

    def floor_for(self, severity, presence) -> int:
        # Minimum score for one conflict
        return self._FLOORS[(self.normalise(severity), self.normalise_presence(presence))]
