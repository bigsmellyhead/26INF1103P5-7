from models.allergen_grp import AllergenGrp
from models.severity_level import SeverityLevel
from models.Restriction import Restriction
from models.allergen_restriction import AllergenRestriction
from models.dietary_restriction import DietaryRestriction
from models.other_restriction import OtherRestriction

class AllergenCatalog:
    __items: dict[str, list[str]]                       # menu category -> the allergens inside it
    __dietary: list[str]                                # halal, vegan, etc.
    __category_to_grp: dict[str, AllergenGrp]           # menu category -> allergen group
    __severity_descriptions: dict[SeverityLevel, str]   # what LOW / MED / HIGH mean
    __default_severity: SeverityLevel                   # used when a severity was never recorded
    __item_to_grp: dict[str, AllergenGrp]               # look up table: each item (lowercase) -> its group
    __known_allergens: set[str]
    __known_dietary: set[str]

    def __init__(self) -> None:
        self.__items = {
            "Cereals containing gluten": ["Wheat", "Rye", "Barley", "Oats", "Spelt", "Kamut"],
            "Crustaceans": ["Prawn", "Shrimp", "Crab", "Lobster", "Crayfish"],
            "Eggs": ["Chicken egg", "Duck egg", "Quail egg"],
            "Fish": ["Salmon", "Tuna", "Cod", "Mackerel", "Sardine", "Anchovy (ikan bilis)"],
            "Peanuts & soybeans": ["Peanut", "Soybean", "Soy sauce", "Tofu", "Tempeh"],
            "Milk & dairy (incl. lactose)": ["Milk", "Lactose", "Cheese", "Butter", "Cream", "Whey", "Casein"],
            "Tree nuts": ["Almond", "Brazil nut", "Cashew", "Hazelnut", "Macadamia",
                          "Pecan", "Pine nut", "Pistachio", "Walnut"]
        }

        self.__dietary = ["Halal", "Kosher", "Vegetarian", "Vegan", "No beef", "No pork"]

        self.__category_to_grp = {
            "Cereals containing gluten": AllergenGrp.CEREAL,
            "Crustaceans": AllergenGrp.CRUSTACEANS,
            "Eggs": AllergenGrp.EGGS,
            "Fish": AllergenGrp.FISH,
            "Peanuts & soybeans": AllergenGrp.PEANUTS_AND_SOYBEANS,
            "Milk & dairy (incl. lactose)": AllergenGrp.MILK_AND_DAIRY,
            "Tree nuts": AllergenGrp.TREE_NUTS,
        }

        #================Severity Section================
        self.__severity_descriptions = {
            SeverityLevel.LOW:  "Discomfort only - bloating, stomach upset, mild itch. Passes on its own.",
            SeverityLevel.MED:  "Clear reaction - hives, swelling, vomiting. May need medication, not life-threatening.",
            SeverityLevel.HIGH: "Life-threatening - airway closing, difficulty breathing, anaphylaxis. Even traces are dangerous.",
        }

        self.__default_severity = SeverityLevel.HIGH #anything not listed

        # look up table; each catalog item (lowercase)
        self.__item_to_grp = {item.lower(): self.__category_to_grp[category]
                              for category, items in self.__items.items() for item in items}
        self.__known_allergens = set(self.__item_to_grp)
        self.__known_dietary = {item.lower() for item in self.__dietary}

    # ---------------- What the menu shows ----------------
    def categories(self) -> dict[str, list[str]]:
        return {category: list(items) for category, items in self.__items.items()}

    # The dietary Restrictions
    def dietary_options(self) -> list[str]:
        return list(self.__dietary)

    # What each severity level means - shown when the user is asked
    def severity_descriptions(self) -> dict[SeverityLevel, str]:
        return dict(self.__severity_descriptions)

    # The level assumed when a severity was never recorded
    def default_severity(self) -> SeverityLevel:
        return self.__default_severity

    # Questions about one name

    def is_allergen(self, name: str) -> bool:
        return name.strip().lower() in self.__known_allergens

    def is_dietary(self, name: str) -> bool:
        return name.strip().lower() in self.__known_dietary

    # True if the name is anywhere in the catalog (False means the user typed it in)
    def is_known(self, name: str) -> bool:
        return self.is_allergen(name) or self.is_dietary(name)

    # The allergen group of an item, or None if it is not a catalog allergen
    def group_of(self, name: str) -> AllergenGrp | None:
        return self.__item_to_grp.get(name.strip().lower())

    # Deciding factor How severely does this affects you
    def needs_severity(self, name: str) -> bool:
        key = name.strip().lower()
        return bool(key) and key != "none" and not self.is_dietary(key)

    # Building things from names 
    def group_restrictions(self, restrictions, severity=None) -> dict:
        severity = severity or {}

        normalised_severity = {
            name.strip().lower(): level
            for name, level in severity.items()
            if isinstance(name, str)
        }

        groups = {
            "allergies": [],
            "dietary_restrictions": [],
            "other": [],
            "severity": {}
        }

        ignored_keys = {
            "allergies",
            "dietary_restrictions",
            "dietary restrictions",
            "other",
            "restrictions",
            "severity",
            "none"
        }

        for item in restrictions:
            key = item.strip().lower()

            if not key or key in ignored_keys:
                continue

            if self.is_allergen(key):
                groups["allergies"].append(key)
            elif self.is_dietary(key):
                groups["dietary_restrictions"].append(key)
            else:
                groups["other"].append(key)

        for name in groups["allergies"] + groups["other"]:
            if name in normalised_severity:
                groups["severity"][name] = normalised_severity[name]

        return groups

    # Turns one name into the right Restriction Object
    def create_restriction(self, name: str, severity=None) -> Restriction:
        key = name.strip().lower() #key meaning the name of the item itself. Eg. Chicken Egg
        if self.is_dietary(key):
            return DietaryRestriction(key)

        level = SeverityLevel(severity) if severity else self.__default_severity #If no severity was given (e.g. an old profile), fall back to Default
        group = self.group_of(key)
        if group:
            return AllergenRestriction(key, group, level)
        return OtherRestriction(key, level)
