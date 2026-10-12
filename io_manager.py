# io_manager.py
from getpass import getpass

from data_manager import get_user_profile, save_user_profile
from logic_manager import search_user_profiles


def get_yes_no_input(prompt):
    """Prompts until the user enters either 'y' or 'n'."""
    while True:
        choice = input(prompt).strip().lower()
        if choice in {"y", "n"}:
            return choice
        print("Error: Please enter 'y' or 'n' only.")


def admin_authentication():
    """Checks the password for the Admin account."""
    return getpass("Enter password: ") == "Admin123"


def handle_user_authentication():
    """Handles existing user check, profile editing, or new user registration."""
    print("\n==============================================")
    print("   HAWKER DIETARY & INGREDIENT SAFETY AUDITOR")
    print("==============================================")
    while True:
        username = input("Enter your username: ").strip()
        if username == "Admin":
            if admin_authentication():
                return username, []
            print("Incorrect password.")
            continue
        if username and all(char.isalnum() or char in {"_", "-"} for char in username):
            break
        print("Invalid username. Use only letters, numbers, underscores, or hyphens.")

    username = username.lower()

    user_profile = get_user_profile(username)

    if user_profile:
        print(f"\nWelcome back, {user_profile['username']}!")
        print(f"Current saved restrictions: {', '.join(user_profile['restrictions'])}")

        # Give the user an option to edit their restrictions
        update_choice = get_yes_no_input("Would you like to update your dietary restrictions? (y/n): ")
        if update_choice == 'y':
            raw_restrictions = input("Enter your allergies/restrictions (e.g., peanuts, seafood): ")

        # Replace commas with spaces, then split by any whitespace
            normalized_text = raw_restrictions.replace(",", " ")
            restrictions = [r.strip().lower() for r in normalized_text.split() if r.strip()]

            if not restrictions:
                restrictions = ["none"]
                # Overwrite the profile in the JSON database
                save_user_profile(username, restrictions)
                print("Profile updated successfully!")
        else:
            restrictions = user_profile['restrictions']
    else:
        print(f"\nNew user detected ('{username}'). Let's set up your dietary profile.")
        raw_restrictions = input("Enter your allergies/restrictions separated by commas (e.g., peanuts, seafood, halal): ")
        restrictions = [r.strip().lower() for r in raw_restrictions.split(",") if r.strip()]
        if not restrictions:
            restrictions = ["none"]
        save_user_profile(username, restrictions)
        print(f"Profile saved successfully for {username}!")

    return username, restrictions

def run_admin_profile_search(username):
    """Offers profile search to Admin and displays matching profiles."""
    if username != "Admin":
        return True

    choice = get_yes_no_input(
        "\n=======================================================\n"
        "   WELCOME TO DATABASE SEARCH. SEARCH USER PROFILES?\n"
        "=======================================================\n"
        "(y/n): "
    )
    if choice == "n":
        return False
    if choice != "y":
        return True

    search_term = input("Enter a name or dietary restriction to search for: ").strip()
    if not search_term:
        print("Search term cannot be blank.")
        return True

    matches = search_user_profiles(search_term)
    if not matches:
        print("No matching user profiles found.")
        return True

    print("\nMatching user profiles:")
    for profile in matches:
        restrictions = ", ".join(profile["restrictions"])
        print(f"- {profile['username']}: {restrictions}")
    return True

def get_user_inputs():
    """Prompts the user for the stall and dish they want to audit."""
    print("\n--- New Dish Audit ---")
    stall = input("Enter Hawker Centre or Stall Name (e.g., Maxwell Food Centre): ").strip()
    dish = input("Enter Dish Name (e.g., Chicken Rice): ").strip()

    return stall, dish

def display_audit_result(username, stall, dish, restrictions, result_data):
    """Displays the final processed audit report clearly to the user."""
    print("\n==============================================")
    print("               AUDIT RESULT REPORT            ")
    print("==============================================")
    print(f"User Profile         : {username} ({', '.join(restrictions)})")
    print(f"Location / Stall     : {stall}")
    print(f"Dish Evaluated       : {dish}")
    print(f"Risk Score           : {result_data.get('risk_score')}%")
    print(f"Risk Level           : {result_data.get('risk_level')}")

    safety_status = "SAFE TO EAT" if result_data.get('is_safe') else "NOT SAFE / AVOID"
    print(f"Safety Status        : [{safety_status}]")

    print(f"Stall Insights       : {result_data.get('stall_specific_insights')}")
    print(f"Hidden Ingredients   : {', '.join(result_data.get('hidden_ingredients', []))}")
    print(f"Reasoning            : {result_data.get('reasoning')}")
    print("----------------------------------------------")
    print("⚠️ ADVISORY DISCLAIMER: This tool is advisory only.")
    print("   Always verify with store owners for safety.")
    print("==============================================\n")