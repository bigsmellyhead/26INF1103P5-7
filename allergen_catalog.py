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
                for cat, items in ALLERGEN_CATALOG.items() for item in items}

#PRESETS OF SEVERITY. lowercase names
SEVERITY_PRESETS = {
    "chicken egg": SeverityLevel.HIGH,
    "peanut": SeverityLevel.HIGH,
    "lactose": SeverityLevel.LOW,
}
DEFAULT_SEVERITY = SeverityLevel.MED #anything not listed above. TO FIX ################################:3

def severity_of(name):
    return SEVERITY_PRESETS.get(name.strip().lower(), DEFAULT_SEVERITY)

def create_restriction(name):
    key = name.strip().lower() #key meaning the name of the item itself. Eg. Chicken Egg
    if key in ITEM_TO_GRP:
        return AllergenRestriction(key, ITEM_TO_GRP[key], severity_of(key))
    if key in KNOWN_DIETARY:
        return DietaryRestriction(key)
    return OtherRestriction


