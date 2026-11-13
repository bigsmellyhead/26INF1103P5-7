from allergen_catalog import ALLERGEN_CATALOG, DIETARY_RESTRICTIONS, KNOWN_ITEMS

#The File for the Menu | What the user inputs to tick the options

class RestrictionMenu: 
    def __init__(self, current=None):
        # Every entry: (group header, menu title, list of items)
        self.__entries = [("Allergies", category, list(items)) for category, items in ALLERGEN_CATALOG.items()]
        self.__entries.append(("Restrictions", "Dietary / Religious", list(DIETARY_RESTRICTIONS)))

        # Continue saved user previous profile. New profile for new users
        self.__selected = {name.strip().lower() for name in (current or []) if name and name != "none"}

        # Items saved earlier that is not in catalog is kept other "Other"
        self.__custom_items = sorted(name for name in self.__selected if name not in KNOWN_ITEMS)

    @property
    def entries(self) -> list:
        return self.__entries

    @property
    def custom_items(self) -> list:
        return self.__custom_items

    # "Other (type your own)"
    @property
    def other_number(self) -> int:
        return len(self.__entries) + 1

    def is_selected(self, item: str) -> bool:
        return item.lower() in self.__selected

    # Ticked items (Eg. "2 selected" tag)
    def count_selected(self, items) -> int:
        return sum(1 for item in items if self.is_selected(item))

    # Everything that is ticked, sorted list. (If empty, nothing)
    def selected_names(self) -> list:
        return sorted(self.__selected)

    # Tick and Untick the user check box
    def toggle(self, items, numbers) -> None:
        #set() so "1,1" doesnt tick and untick the same item
        for number in set(numbers):
            item = items[number - 1].lower()
            if item in self.__selected:
                self.__selected.remove(item)
            else:
                self.__selected.add(item)

    def select_all(self, items) -> None:
        self.__selected.update(item.lower() for item in items)

    def select_none(self, items) -> None:
        self.__selected.difference_update(item.lower() for item in items)

    def clear(self) -> None:
        self.__selected.clear()

    # Adds custom allergens ("Eg. Blue Berries") and tick
    def add_custom(self, raw_text: str) -> None:
        for new_item in self.__split_by_commas(raw_text):
            if new_item == "none":
                continue
            if new_item not in self.__custom_items:
                self.__custom_items.append(new_item)
            self.__selected.add(new_item)

    # Turns "1, 3 4" into [1, 3, 4]. Returns None if any invalid
    def parse_numbers(self, raw_text: str, max_value: int):
        parts = raw_text.replace(",", " ").split()
        if not parts or not all(p.isdigit() for p in parts):
            return None
        numbers = [int(p) for p in parts]
        if any(n < 1 or n > max_value for n in numbers):
            return None
        return numbers

    #split commas seperated input and into lowercase
    def __split_by_commas(self, raw_text: str) -> list:
        return [part.strip().lower() for part in raw_text.split(",") if part.strip()]

