# io_manager.py
from data_manager import get_user_profile, save_user_profile
from allergen_catalog import ALLERGEN_CATALOG, DIETARY_RESTRICTIONS, KNOWN_ITEMS , group_restrictions

DIVIDER = "=" * 100
SECTION = "-" * 100
# ANSI Colour definitions
COLOR_RED = "\033[31m"
COLOR_YELLOW = "\033[33m"
COLOR_GREEN = "\033[32m"
COLOR_RESET= "\033[0m"

CUSTOM_PROMPT = (
    # --- Prompt for anything not in the catalog ---
    "Type your own allergies/restrictions, separated by commas\n"
    "(e.g. g6pd, blue berries): ")

"""!
@brief   - Prints the structured summary of a user's allergies, dietary restrictions, and other flags.
@details - Extracts and sequentially prints to stdout from sub-lists from the parameter 'restrictions' in the following order:
           1. Allergies
           2. Dietary Restrictions
           3. Others
           *Prints 'None' for any empty lists

@param restrictions - A dictionary containing lists mapping to the keys "allergies", "dietary_restrictions", and "others".
@return None
"""
def print_user_restrictions(restrictions):
    categories = [
        ("allergies", "Allergies"),
        ("dietary_restrictions", "Dietary Restrictions"),
        ("others", "Others")
    ]
    for key, label in categories:
        items = restrictions.get(key, [])
        if not items:
            print(f"  • {label}: None")
        else:
            print(f"  • {label}:")
            for item in items:
                print(f"    - {item}")
    print("")

"""!
@brief   -  Evaluates and prints a colored risk assessment statement alongside safety verdicts.
@details -  Processes execution fields to dynamically evaluate severity thresholds. 
            It utilizes a Python match-case block to match 'High', 'Medium', or 'Low' text levels to terminal color constants, 
            then prints a final binary safety verdict ('SAFE TO EAT' vs 'NOT SAFE / AVOID') alongside contextual logic reasoning.

@param result_data - A dictionary containing  keys: 'risk_level' (str), 'is_safe' (bool), 'risk_score' (int/float), and 'reasoning' (str).
@note - Utilizes local ANSI constants (`COLOR_RED`, `COLOR_YELLOW`, `COLOR_GREEN`, `COLOR_RESET`) to output color metrics into the terminal interface.
@return None
"""
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
    print(f"{CURRENT_COLOR}Risk Assessment: {result_data.get('risk_score')}% ({result_data.get('risk_level')})")
    print(f"VERDICT: {safety_status}")
    print(f"Reasoning:")
    print(f"{result_data.get('reasoning')}\n    {COLOR_RESET}")

"""!
@brief   - Prints the Allergen Conflicts to stdout
@details - Extracts and prints detected allergy conflicts from result_data. 
           *Prints 'None' if no conflicts are found, or lists each violation.

@param result_data - Dictionary containing 'allergy_conflicts' key 
@return None
"""
def print_allergy_conflicts(result_data):
    conflicts = result_data.get("allergy_conflicts",[])

    if not conflicts:
        print("🚨 DETECTED CONFLICTS: None")
    else:
        print("🚨 DETECTED CONFLICTS:")
        for conflict in conflicts:
            print(f"• [ALLERGY VIOLATION] {conflict} detected in ingredient breakdown.")

"""!
@brief   - Prints the Dietary Status to stdout
@details - Extracts and prints dietary status flags and values from result_data.
           *Prints 'None' if the status is empty, or lists each key-value pair.

@param result_data - Dictionary containing 'dietary_status' key
@return None
"""
def print_dietary_status(result_data):
    dietary_status = result_data.get("dietary_status",{})
    
    if not dietary_status:
        print("🌿 DIETARY STATUS: None")
    else:
        print("🌿 DIETARY STATUS:")
        for key , value in dietary_status.items():
            print(f"• {key}: {value}")

"""!
@brief   - Prints the Cross-Contamination Risks to stdout
@details - Extracts and prints cross-contamination risks from result_data.
           *Prints 'None' if the list is empty, or lists each risk.

@param result_data - Dictionary containing 'cross_contact_risks' key
@return None
"""
def print_cross_contact_risks(result_data):
    cross_contact_risks = result_data.get("cross_contact_risks",[])
    if not cross_contact_risks:
        print("⚠️  Cross-Contamination Risks: None")
    else:
        print("⚠️  Cross-Contamination Risks:")
        for risk in cross_contact_risks:
            print(f"• [ENVIRONMENTAL RISK] {risk}")

"""!
@brief   - Prints the full ingredient breakdown and traceability tree to stdout
@details - Checks for valid result data, prints the section header, extracts the root 
           dish name from the 'ingredient_tree', and initiates the recursive 
           child tree printing function.

@param result_data - Dictionary containing the 'ingredient_tree' key mapping to the root node.
@return None
"""
def print_ingredient_breakdown_tree(result_data):
    if not result_data:
        return

    print(f"{SECTION}")
    print("🌳 FULL INGREDIENT BREAKDOWN & TRACEABILITY:")
    print(f"{SECTION}")
    ingredient_list = result_data.get("ingredient_tree")
    print(f"Dish: {ingredient_list["name"]}")
    print_children_tree(ingredient_list, "")

"""!
@brief   - Recursively prints the child nodes of an ingredient tree with structural tree lines
@details - Iterates through the children of a starting node, checks their status and 
           conflict state to apply color formatting, and recursively processes nested 
           sub-children with proper indentation and tree branching symbols (├── and └──).

@param starting_node - Dictionary representing the current node (contains 'name', 'status', 'conflict', and optionally 'children').
@param prefix        - String used for tracking recursive indentation and tree alignment.
@return None
"""

def has_triggered_descendant(node):
    """Recursively checks if a node or any of its descendants is a trigger with a conflict or triggered children."""
    if node.get("conflict") and node.get("status") == "Trigger":
        return True
    for child in node.get("children", []):
        if has_triggered_descendant(child):
            return True
    return False

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

        # Factor in whether the node itself has a conflict or has triggered descendants
        if child_status == "Trigger" and (child_conflict or has_triggered_descendant(child)):
            if child_conflict:
                child_verdict = f"{COLOR_RED}<-----[{child_status}: {child_conflict}]{COLOR_RESET}"
            else:
                child_verdict = f"{COLOR_RED}({child_status}){COLOR_RESET}"
        else:
            child_verdict = f"{COLOR_GREEN}({child_status}){COLOR_RESET}"

        if(index == len(children) - 1):
             print(f"{prefix}{symbol_endTree}{child_name} {child_verdict}")
             indentation = "    "
        else:
             print(f"{prefix}{symbol_startTree}{child_name} {child_verdict}")
             indentation = "│   "

        # Show the stall-specific note under the ingredient it applies to
        child_insight = child.get("stall_insight")
        if child_insight:
            print(f"{prefix}{indentation}↳ {COLOR_YELLOW}Stall: {child_insight}{COLOR_RESET}")
            
        if("children" in child):
            print_children_tree(child, prefix + indentation)


"""!
@brief   - Displays the final processed audit report clearly to the user
@details - Compiles and prints a comprehensive dish safety audit to stdout. 
           This includes user profile/restrictions, stall details, knowledge status, 
           risk assessment, allergy conflicts, dietary status, cross-contamination 
           risks, and the full ingredient breakdown tree, followed by an advisory disclaimer.

@param username    - The name of the user requesting the audit.
@param stall       - The location or stall name where the dish is served.
@param dish        - The name of the dish being audited.
@param restrictions - A dictionary containing the user's dietary restrictions and allergies.
@param result_data  - A dictionary containing audit results (stall knowledge, insights, conflicts, tree, etc.).
@return None
"""
def display_audit_result(username, stall, dish, restrictions, result_data):
    stall_knowledge = result_data["stall_knowledge"]
    stall_emoji = "🟢" if stall_knowledge == "Known" else "🟡" if stall_knowledge == "Inferred" else "🔴"
    """Displays the final processed audit report clearly to the user."""
    print(f"{DIVIDER}")
    print("                         DISH SAFETY AUDIT            ")
    print(f"{DIVIDER}")

    # User and Restrictions section
    print(f"[USERNAME] {username}")
    print(f"[USER PROFILE & RESTRICTIONS]")
    print_user_restrictions(restrictions)

    # Stall and Insights Section
    print(f"[DISH] {dish}")
    print(f"[LOCATION/STALL] {stall}\n")
    print(f"[STALL STATUS: {stall_knowledge} {stall_emoji}]")
    print(f"[Stall Insights]")
    print(f"{result_data.get('stall_specific_insights')}\n")

    # Risk Assessment Section
    print(f"{SECTION}")
    print_risk_assessment(result_data)
    print_allergy_conflicts(result_data)
    print("")
    print_dietary_status(result_data)
    print("")
    print_cross_contact_risks(result_data)
    print("")

    # Ingredient Breakdown Section
    print_ingredient_breakdown_tree(result_data)

    print(f"\n{DIVIDER}")
    print("⚠️  ADVISORY DISCLAIMER: This tool is advisory only.")
    print("   Always verify with store owners for safety.")
    print(f"{DIVIDER}")

# Input handling for restrictions
def parse_restrictions(raw_text):
    # --- Spliting of Allergies / Restrictions by commas "," ---
    """Split comma-separated input into a clean list. Returns ['none'] if empty."""
    items = [r.strip().lower() for r in raw_text.split(",") if r.strip()]
    return items if items else ["none"]

def parse_number_list(raw_text, max_value):
    # --- Turns "1, 3 4" into [1, 3, 4]. Returns None if anything is invalid ---
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
    # --- Level 2: tick / untick specific allergens inside one category ---
    # `selected` (a set) and `items` (a list) are edited in place.
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
            # set() so "1,1" doesn't tick and untick the same item
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
            restrictions = group_restrictions(restrictions)
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
        # Reformat the restrictions to group them according:
        # Allergens
        # Dietary Restrictions
        # Others
        restrictions = group_restrictions(restrictions)
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

# --- AI Error Display Helpers ---
def display_api_key_error():
    print("[AI Manager] GEMINI_API_KEY is not set. Please set it in your .env file.")

def display_attempt_error(attempt, max_tries, error):
    print(f"[AI Manager] Attempt {attempt}/{max_tries} failed: {error}")