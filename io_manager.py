# io_manager.py
from data_manager import get_user_profile, save_user_profile
from allergen_catalog import ALLERGEN_CATALOG, DIETARY_RESTRICTIONS, KNOWN_ITEMS

DIVIDER = "=" * 70
SECTION = "-" * 70
COLOR_RED = "\033[31m"
COLOR_YELLOW = "\033[33m"
COLOR_GREEN = "\033[32m"
COLOR_RESET= "\033[0m"

CUSTOM_PROMPT = (
    # --- Prompt for anything not in the catalog ---
    "Type your own allergies/restrictions, separated by commas\n"
    "(e.g. g6pd, blue berries): ")

def print_user_restrictions(restrictions):
    print(f"  • Allergies & Dietary Needs")
    for restriction in restrictions:
        print(f"    - {restriction}")
    print("")

def print_risk_assessment(result_data):
    # ANSI Colour definitions
    CURRENT_COLOR = ""
    #Analyse Risk Score and assign color codes based on risk score
    match(result_data.get('risk_level')):
        case('High'):
            CURRENT_COLOR = COLOR_RED
        case("Medium"):
            CURRENT_COLOR = COLOR_YELLOW
        case("Low"):
            CURRENT_COLOR = COLOR_GREEN

    safety_status = "SAFE TO EAT" if result_data.get('is_safe') else "NOT SAFE / AVOID"
    print(f"{CURRENT_COLOR}----------------------------------------------------------------------")
    print(f"Risk Assessment: {result_data.get('risk_score')}% ({result_data.get('risk_level')})")
    print(f"VERDICT: {safety_status}")
    print(f"----------------------------------------------------------------------{COLOR_RESET}\n")

def print_allergy_conflicts(result_data):
    if(len(result_data.get("allergy_conflicts")) == 0):
        print("DETECTED CONFLICTS:")
        print("* None")
    else:
        print("🚨 DETECTED CONFLICTS:")
        for conflict in result_data.get("allergy_conflicts"):
            print(f"* [ALLERGY VIOLATION] {conflict} detected in ingredient breakdown.")

def print_dietary_status(result_data):
    print("🌿 DIETARY STATUS:")
    if(len(result_data.get("dietary_status")) == 0):
        print("* None")
    else:
        for key , value in result_data.get("dietary_status").items():
            print(f"* {key}: {value}")
    
# Output hidden ingredients in a tree format
def print_ingredient_breakdown_tree(result_data):
    if not result_data:
        return

    print("----------------------------------------------------------------------")
    print("🌳 FULL INGREDIENT BREAKDOWN & TRACEABILITY:")
    print("----------------------------------------------------------------------")
    ingredient_list = result_data.get("ingredient_tree")
    print(f"Dish: {ingredient_list["name"]}")
    print_children_tree(ingredient_list, "")

#ingredient list is a dictionary
def print_children_tree(starting_node, prefix = ""):
    children = starting_node["children"]

    symbol_startTree = "├── "
    symbol_endTree = "└── "
    indentation = ""
    #Loop through the children
    for index, child in enumerate(children):
        child_name = child["name"]
        child_status = child["status"]
        child_conflict = child["conflict"]
        child_verdict = ""

        if(child_conflict and child_status == "Trigger"):
            child_verdict = f"{COLOR_RED}<-----[{child_status}: {child_conflict}]{COLOR_RESET}"
        else:
            child_verdict = f"{COLOR_GREEN}({child_status}){COLOR_RESET}"

        if(index == len(children) - 1):
             print(f"{prefix}{symbol_endTree}{child_name} {child_verdict}")
             indentation = "    "
        else:
             print(f"{prefix}{symbol_startTree}{child_name} {child_verdict}")
             indentation = "│   "

        if child["children"]:
            print_children_tree(child, prefix + indentation)


# Output the final audit result to the user in a clear format
def display_audit_result(username, stall, dish, restrictions, result_data):
    """Displays the final processed audit report clearly to the user."""
    print("======================================================================")
    print("                         DISH SAFETY AUDIT            ")
    print("======================================================================")
    print(f"[DISH] {dish}")
    print(f"[LOCATION/STALL] {stall}\n")
    
    print(f"[USERNAME] {username}")
    print(f"[USER PROFILE & RESTRICTIONS]")
    print_user_restrictions(restrictions)
    print_risk_assessment(result_data)

    print_allergy_conflicts(result_data)
    print("")
    print_dietary_status(result_data)
    print("")
    print_ingredient_breakdown_tree(result_data)

    #print(f"Stall Insights: ")
    #print(f"{result_data.get('stall_specific_insights')}\n")

    #print_hidden_ingredients_tree(result_data)
    
    #print(f"Reasoning:")
    #print(f"{result_data.get('reasoning')}\n    ")

    print("\n======================================================================")
    print("⚠️  ADVISORY DISCLAIMER: This tool is advisory only.")
    print("   Always verify with store owners for safety.")
    print("======================================================================")

# Input handling for restrictions
def parse_restrictions(raw_text):
    # --- Spliting of Allergies / Restrictions by commas "," ---
    """Split comma-separated input into a clean list. Returns ['none'] if empty."""
    items = [r.strip().lower() for r in raw_text.split(",") if r.strip()]
    return items if items else ["none"]

def parse_number_list(raw_text, max_value):
    parts = raw_text.replace(",", " ").split()
    if not parts or not all(p.isdigit() for p in parts):
        return None
    numbers = [int(p) for p in parts]
    if any(n < 1 or n > max_value for n in numbers):
        return None
    return numbers

def show_category_menu(menu_entries, selected, custom_items):
    # --- Level 1: Allergies first, then Restrictions, then Other ---
    # menu_entries is a list of (group, title, items) tuples
    print(f"\n{SECTION}")
    print(" SELECT YOUR ALLERGIES / RESTRICTIONS")
    print(SECTION)

    last_group = None
    for number, (group, title, items) in enumerate(menu_entries, start=1):
        # Print a group header (ALLERGIES / RESTRICTIONS) whenever the group changes
        if group != last_group:
            print(f"\n  {group.upper()}")
            last_group = group

        ticked = sum(1 for item in items if item.lower() in selected)
        tag = f"  ({ticked} selected)" if ticked else ""
        print(f"    {number}. {title}{tag}")

    ticked_custom = sum(1 for item in custom_items if item in selected)
    tag = f"  ({ticked_custom} selected)" if ticked_custom else ""
    print("\n  OTHER")
    print(f"    {len(menu_entries) + 1}. Other (type your own){tag}")

    print("\n  Enter a number to open it.")
    print("  D = Done    C = Clear everything")
    print(f"\nCurrently selected: {', '.join(sorted(selected)) if selected else 'none'}")

def run_item_menu(title, items, selected, allow_custom=False):

    while True:
        print(f"\n{SECTION}")
        print(f" {title}")
        print(SECTION)

        if not items:
            print("  (nothing here yet)")
        for number, item in enumerate(items, start=1):
            mark = "x" if item.lower() in selected else " "
            print(f"  {number}. [{mark}] {item}")

        print("\n  Enter numbers to tick/untick (e.g. 1,3)")
        extras = "  A = Select all    N = Select none"
        if allow_custom:
            extras += "    T = Type a new one"
        print(extras)
        print("  B = Back")

        choice = input("Your choice: ").strip().lower()

        if choice == "b":
            return
        elif choice == "a":
            selected.update(item.lower() for item in items)
        elif choice == "n":
            selected.difference_update(item.lower() for item in items)
        elif choice == "t" and allow_custom:
            raw = input(CUSTOM_PROMPT)
            for new_item in parse_restrictions(raw):
                if new_item == "none":
                    continue
                if new_item not in items:
                    items.append(new_item)
                selected.add(new_item)
        else:
            numbers = parse_number_list(choice, len(items))
            if numbers is None:
                print("Invalid choice. Please try again.")
                continue
            
            for number in set(numbers):
                item = items[number - 1].lower()
                if item in selected:
                    selected.remove(item)
                else:
                    selected.add(item)

def prompt_for_restrictions(current=None):
    # --- Prompts the user for Restrictions via the category menu and Returns them ---
    """Walks the user through the allergen menu. Returns a clean list, or ['none']."""
    # Each entry: (group header, menu title, list of items)
    menu_entries = [("Allergies", category, items) for category, items in ALLERGEN_CATALOG.items()]
    menu_entries.append(("Restrictions", "Dietary / religious", DIETARY_RESTRICTIONS))
    other_number = len(menu_entries) + 1

    # Start from whatever the user already has saved (empty for new users)
    selected = {r for r in (current or []) if r != "none"}

    # Anything saved earlier that isn't in the catalog is kept under "Other"
    custom_items = sorted(r for r in selected if r not in KNOWN_ITEMS)

    while True:
        show_category_menu(menu_entries, selected, custom_items)
        choice = input("Your choice: ").strip().lower()

        if choice == "d":
            break
        elif choice == "c":
            selected.clear()
        elif choice.isdigit() and 1 <= int(choice) <= len(menu_entries):
            group, title, items = menu_entries[int(choice) - 1]
            run_item_menu(f"{group} > {title}", items, selected)
        elif choice.isdigit() and int(choice) == other_number:
            run_item_menu("Other", custom_items, selected, allow_custom=True)
        else:
            print("Please enter a number, 'd' or 'c'.")

    return sorted(selected) if selected else ["none"]

# Input handling for user authentication
def handle_user_authentication():
    """Handles existing user check, profile editing, or new user registration."""

    # --- App banner ---
    print(f"\n{DIVIDER}")
    print("   HAWKER DIETARY & INGREDIENT SAFETY AUDITOR")
    print(f"{DIVIDER}\n")

    # --- Get and validate username ---
    username = input("Enter your username: ").strip()

    if not username:
        # Fall back to a default rather than letting an empty username through
        print("\nUsername cannot be empty. Defaulting to 'guest'.")
        username = "guest"

    # Look up this username in the saved profiles (returns None if new)
    user_profile = get_user_profile(username)

    if user_profile:
        # --- Existing user: show their saved data ---
        print(f"\nWelcome back, {user_profile['username']}!")
        print(f"Current saved restrictions: {', '.join(user_profile['restrictions'])}\n")

        # Loop until the user gives a valid y/n answer
        while True:
            update_choice = input("Would you like to update your dietary restrictions? (y/n): ").strip().lower()
            if update_choice in ['y', 'n']:
                break
            print("Please enter only 'y' or 'n'.")

        if update_choice == 'y':
            # --- User wants to change their restrictions (menu opens pre-ticked) ---
            restrictions = prompt_for_restrictions(current=user_profile['restrictions'])

            # Overwrite the profile in the JSON database
            save_user_profile(username, restrictions)
            print(f"\nProfile updated! Saved {len(restrictions)} restriction(s): {', '.join(restrictions)}")
        else:
            # --- User declined to update: keep existing restrictions as-is ---
            print("No updates made.")
            restrictions = user_profile['restrictions']
    else:
        # --- New user: walk them through initial setup ---
        print(f"\nNew user detected ('{username}'). Let's set up your dietary profile.")
        restrictions = prompt_for_restrictions()

        # Create the profile for the first time
        save_user_profile(username, restrictions)
        print(f"\nProfile saved for {username}! Saved {len(restrictions)} restriction(s): {', '.join(restrictions)}")

    # Hand back the username and their current (possibly just-updated) restrictions
    return username, restrictions

# Input handling for stall and dish
def get_user_inputs():
    """Prompts the user for the stall and dish they want to audit."""
    # --- Audit section header ---
    print(f"\n{SECTION}")
    print(" NEW DISH AUDIT")
    print(f"{SECTION}\n")

    # --- Collect the two pieces of info needed to run the audit ---
    stall = input("Enter Hawker Centre or Stall Name (e.g., Maxwell Food Centre): ").strip()
    dish = input("Enter Dish Name (e.g., Chicken Rice): ").strip()

    return stall, dish