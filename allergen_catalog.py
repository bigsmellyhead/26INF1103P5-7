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

    groups = {"allergies": [], "restrictions": [], "other": []}

    ###

    return groups