# io_manager.py
from data_manager import get_user_profile, save_user_profile

DIVIDER = "=" * 46
SECTION = "-" * 46
COLOR_RED = "\033[31m"
COLOR_YELLOW = "\033[33m"
COLOR_GREEN = "\033[32m"
COLOR_RESET= "\033[0m"

RESTRICTIONS_PROMPT = (
    # --- Prompt for User ---
    "Enter your allergies/restrictions, separated by commas\n"
    "(e.g. peanuts, seafood, g6pd, tree nuts): ")

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
        case(Low):
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

    print("----------------------------------------------------------------------\n")
    print_allergy_conflicts(result_data)
    print("")
    print_dietary_status(result_data)
    print("\n----------------------------------------------------------------------")

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

# Input restrictions display
def prompt_for_restrictions():
    # --- Prompts the user for Restrictions and Returns ---
    """Asks the user for their restrictions and returns them as a clean list."""
    raw_restrictions = input(RESTRICTIONS_PROMPT)
    return parse_restrictions(raw_restrictions)

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
            # --- User wants to overwrite their restrictions ---
            print()
            restrictions = prompt_for_restrictions()

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