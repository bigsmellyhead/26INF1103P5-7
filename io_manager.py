# io_manager.py
from data_manager import get_user_profile, save_user_profile

DIVIDER = "=" * 46
SECTION = "-" * 46

RESTRICTIONS_PROMPT = (
    # --- Prompt for User ---
    "Enter your allergies/restrictions, separated by commas\n"
    "(e.g. peanuts, seafood, g6pd, tree nuts): ")


# Output hidden ingredients in a tree format
def print_hidden_ingredients_tree(result_data):
    symbol_startTree = "├── "
    symbol_endTree = "└── "

    print("---------------------------------------------------------")
    print("🔍  Trigger Breakdown")
    print("---------------------------------------------------------")

   
    allergen_list = result_data.get('hidden_ingredients') or []

     # Fallback if the AI returned a flat list of strings instead of dicts

    if allergen_list and all(isinstance(item, str) for item in allergen_list):
        allergen_list = [{"Hidden ingredients": allergen_list}]

    for i, allergen_dict in enumerate(allergen_list):
        if not isinstance(allergen_dict, dict):
            continue

        is_last_allergen = (i == len(allergen_list) - 1)
        branch = symbol_endTree if is_last_allergen else symbol_startTree
        indent = 5 * " " if is_last_allergen else "│" + 4 * " "

        for allergen, ingredients in allergen_dict.items():
            print(branch + "[" + allergen + "]")
            for j, ingredient in enumerate(ingredients):
                leaf = symbol_endTree if j == len(ingredients) - 1 else symbol_startTree
                print(indent + leaf + "[" + ingredient + "]")

# Output the final audit result to the user in a clear format
def display_audit_result(username, stall, dish, restrictions, result_data):

    COLOR_RED = "\033[31m"
    COLOR_RESET= "\033[0m"


    """Displays the final processed audit report clearly to the user."""
    print("=========================================================")
    print("               AUDIT RESULT REPORT            ")
    print("=========================================================")
    print(f"User Profile         : {username} ({', '.join(restrictions)})")
    print(f"Location / Stall     : {stall}")
    print(f"Dish Evaluated       : {dish}\n")

    print("=========================================================")
    print("Risk Assessment:")
    print("=========================================================\n")
    print(f"Risk Score           : {result_data.get('risk_score')}%")
    print(f"Risk Level           : {COLOR_RED}{result_data.get('risk_level')}{COLOR_RESET}")
    safety_status = "SAFE TO EAT" if result_data.get('is_safe') else "NOT SAFE / AVOID"
    print(f"Safety Status        : [{safety_status}]\n")
    
    print(f"Stall Insights: ")
    print(f"{result_data.get('stall_specific_insights')}\n")

    print_hidden_ingredients_tree(result_data)

    print(f"Reasoning:")
    print(f"{result_data.get('reasoning')}\n    ")
    print("----------------------------------------------")
    print("⚠️  ADVISORY DISCLAIMER: This tool is advisory only.")
    print("   Always verify with store owners for safety.")
    print("==============================================\n")

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