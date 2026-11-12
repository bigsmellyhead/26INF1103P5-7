from allergen_grp import AllergenGrp
from severity_level import SeverityLevel
from allergen_restriction import AllergenRestriction
from dietary_restriction import DietaryRestriction
from other_restriction import OtherRestriction

ALLERGEN_CATALOG = {
    "Cereals containing gluten": ["Wheat", "Rye", "Barley", "Oats", "Spelt", "Kamut"],
    "Crustaceans": ["Prawn", "Shrimp", "Crab", "Lobster", "Crayfish"],
    "Eggs": ["Chicken egg", "Duck egg", "Quail egg"],
    "Fish": ["Salmon", "Tuna", "Cod", "Mackerel", "Sardine", "Anchovy (ikan bilis)"],
    "Peanuts & soybeans": ["Peanut", "Soybean", "Soy sauce", "Tofu", "Tempeh"],
    "Milk & dairy (incl. lactose)": ["Milk", "Lactose", "Cheese", "Butter", "Cream", "Whey", "Casein"],
    "Tree nuts": ["Almond", "Brazil nut", "Cashew", "Hazelnut", "Macadamia",
                  "Pecan", "Pine nut", "Pistachio", "Walnut"]
}


DIETARY_RESTRICTIONS = ["Halal", "Kosher", "Vegetarian", "Vegan", "No beef", "No pork"]

KNOWN_ALLERGENS = {
    item.lower()
    for items in ALLERGEN_CATALOG.values()
    for item in items
}
KNOWN_DIETARY = {item.lower() for item in DIETARY_RESTRICTIONS}

KNOWN_ITEMS = KNOWN_ALLERGENS | KNOWN_DIETARY

def group_restrictions(restrictions):
    ignored_keys = {"allergies", "dietary_restrictions", "dietary restrictions", "other", "restrictions", "none"}
    groups = {"allergies": [], "dietary_restrictions": [], "other": []}

    for item in restrictions:
        key = item.strip().lower()
        if not key or key in ignored_keys:
            continue
        if key in KNOWN_ALLERGENS:
            groups["allergies"].append(key)
        elif key in KNOWN_DIETARY:
            groups["dietary_restrictions"].append(key)
        else:
            groups["other"].append(key)
 

    return groups

#================Severity Section================
SEVERITY_DESCRIPTIONS = {
    SeverityLevel.LOW:  "Discomfort only - bloating, stomach upset, mild itch. Passes on its own.",
    SeverityLevel.MED:  "Clear reaction - hives, swelling, vomiting. May need medication, not life-threatening.",
    SeverityLevel.HIGH: "Life-threatening - airway closing, difficulty breathing, anaphylaxis. Even traces are dangerous.",
}

DEFAULT_SEVERITY = SeverityLevel.HIGH #anything not listed 

CATEGORY_TO_GRP = {
    "Cereals containing gluten": AllergenGrp.CEREAL,
    "Crustaceans": AllergenGrp.CRUSTACEANS,
    "Eggs": AllergenGrp.EGGS,
    "Fish": AllergenGrp.FISH,
    "Peanuts & soybeans": AllergenGrp.PEANUTS_AND_SOYBEANS,
    "Milk & dairy (incl. lactose)": AllergenGrp.MILK_AND_DAIRY,
    "Tree nuts": AllergenGrp.TREE_NUTS,
}

ITEM_TO_GRP = {item.lower(): CATEGORY_TO_GRP[cat]
                for cat, items in ALLERGEN_CATALOG.items() for item in items} # look up table; each catalog item, see if the allergen grp belongs to eg. "chicken eggs", etc

def needs_severity(name): # Decides whether to ask the "How severely does this affect you?" question
    key = name.strip().lower()
    return bool(key) and key != "none" and key not in KNOWN_DIETARY

def group_restrictions(restrictions, severity=None): #Sorts a flat list of names into the dictionary that gets saved to the database
    severity = severity or {}
    ignored_keys = {"allergies", "dietary_restrictions", "dietary restrictions", "other", "restrictions", "severity", "none"} #skipped
    groups = {"allergies": [], "dietary_restrictions": [], "other": [], "severity": {}} 

    for item in restrictions: #To put every name into the right list
        key = item.strip().lower()
        if not key or key in ignored_keys:
            continue                                   #skip blanks and label words
        if key in KNOWN_ALLERGENS:
            groups["allergies"].append(key)            # in the allergen catalog
        elif key in KNOWN_DIETARY:
            groups["dietary_restrictions"].append(key) # halal, vegan, etc.
        else:
            groups["other"].append(key)                # custom. typed in by the user

        # Keep Severity only for items that are actually in the profile
        for name in groups["allergies"] + groups["other"]:
            if name in severity:
                groups["severity"][name] = severity[name]

        return groups    

def create_restriction(name, severity=None):
    key = name.strip().lower() #key meaning the name of the item itself. Eg. Chicken Egg
    if key in KNOWN_DIETARY:
        return DietaryRestriction(key)

    level = SeverityLevel(severity) if severity else DEFAULT_SEVERITY #If no severity was given (e.g. an old profile), fall back to DEFAULT_SEVERITY
    if key in ITEM_TO_GRP:
        return AllergenRestriction(key, ITEM_TO_GRP[key], level)
    return OtherRestriction(key, level)


