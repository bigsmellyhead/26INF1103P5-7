# io_manager.py

from getpass import getpass

from data_manager import get_user_profile, save_user_profile
from logic_manager import search_user_profiles
from allergen_catalog import (
    ALLERGEN_CATALOG,
    DIETARY_RESTRICTIONS,
    KNOWN_ITEMS,
    group_restrictions
)

DIVIDER = "=" * 100
SECTION = "-" * 100

# ANSI colour definitions
COLOR_RED = "\033[31m"
COLOR_YELLOW = "\033[33m"
COLOR_GREEN = "\033[32m"
COLOR_RESET = "\033[0m"

CUSTOM_PROMPT = (
    "Type your own allergies/restrictions, separated by commas\n"
    "(e.g. g6pd, blue berries): "
)


# ============================================================
# USER INPUT HELPERS
# ============================================================

def get_yes_no_input(prompt):
    """Prompt until the user enters y or n."""
    while True:
        choice = input(prompt).strip().lower()
        if choice in {"y", "n"}:
            return choice
        print("Please enter only 'y' or 'n'.")


def admin_authentication():
    """Check the admin password."""
    return getpass("Enter password: ") == "Admin123"


# ============================================================
# DISPLAY RESTRICTIONS
# ============================================================

def print_user_restrictions(restrictions):
    """Display allergies, dietary restrictions, and other flags."""
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


def print_risk_assessment(result_data):
    """Display the risk score, risk level, and safety verdict."""
    match result_data.get("risk_level"):
        case "High":
            current_color = COLOR_RED
        case "Medium":
            current_color = COLOR_YELLOW
        case "Low":
            current_color = COLOR_GREEN
        case _:
            current_color = COLOR_RESET

    safety_status = (
        "SAFE TO EAT"
        if result_data.get("is_safe")
        else "NOT SAFE / AVOID"
    )

    print(
        f"{current_color}Risk Assessment: "
        f"{result_data.get('risk_score')}% "
        f"({result_data.get('risk_level')})"
    )
    print(f"VERDICT: {safety_status}")
    print("Reasoning:")
    print(f"{result_data.get('reasoning')}{COLOR_RESET}\n")


def print_allergy_conflicts(result_data):
    """Display detected allergy conflicts."""
    conflicts = result_data.get("allergy_conflicts", [])

    if not conflicts:
        print("🚨 DETECTED CONFLICTS: None")
    else:
        print("🚨 DETECTED CONFLICTS:")
        for conflict in conflicts:
            print(
                f"• [ALLERGY VIOLATION] {conflict} "
                "detected in ingredient breakdown."
            )


def print_dietary_status(result_data):
    """Display dietary status."""
    dietary_status = result_data.get("dietary_status", {})

    if not dietary_status:
        print("🌿 DIETARY STATUS: None")
    else:
        print("🌿 DIETARY STATUS:")
        for key, value in dietary_status.items():
            print(f"• {key}: {value}")


def print_cross_contact_risks(result_data):
    """Display cross-contamination risks."""
    risks = result_data.get("cross_contact_risks", [])

    if not risks:
        print("⚠️ Cross-Contamination Risks: None")
    else:
        print("⚠️ Cross-Contamination Risks:")
        for risk in risks:
            print(f"• [ENVIRONMENTAL RISK] {risk}")


# ============================================================
# INGREDIENT TREE
# ============================================================

def print_ingredient_breakdown_tree(result_data):
    """Display the complete ingredient breakdown tree."""
    if not result_data:
        return

    print(SECTION)
    print("🌳 FULL INGREDIENT BREAKDOWN & TRACEABILITY:")
    print(SECTION)

    ingredient_list = result_data.get("ingredient_tree")

    if not ingredient_list:
        print("No ingredient breakdown available.")
        return

    print(f"Dish: {ingredient_list['name']}")
    print_children_tree(ingredient_list, "")


def print_children_tree(starting_node, prefix=""):
    """Recursively display ingredient tree nodes."""
    children = starting_node.get("children", [])

    for index, child in enumerate(children):
        child_name = child.get("name", "Unknown")
        child_status = child.get("status", "Unknown")
        child_conflict = child.get("conflict")
        is_last = index == len(children) - 1

        symbol = "└── " if is_last else "├── "
        indentation = "    " if is_last else "│   "

        if child_conflict and child_status == "Trigger":
            verdict = (
                f"{COLOR_RED}<-----"
                f"[{child_status}: {child_conflict}]"
                f"{COLOR_RESET}"
            )
        else:
            verdict = (
                f"{COLOR_GREEN}({child_status}){COLOR_RESET}"
            )

        print(f"{prefix}{symbol}{child_name} {verdict}")

        stall_insight = child.get("stall_insight")
        if stall_insight:
            print(
                f"{prefix}{indentation}↳ "
                f"{COLOR_YELLOW}Stall: {stall_insight}"
                f"{COLOR_RESET}"
            )

        if child.get("children"):
            print_children_tree(
                child,
                prefix + indentation
            )


# ============================================================
# FINAL AUDIT REPORT
# ============================================================

def display_audit_result(
    username, stall, dish, restrictions, result_data
):
    """Display the complete dish safety audit report."""
    stall_knowledge = result_data["stall_knowledge"]

    if stall_knowledge == "Known":
        stall_emoji = "🟢"
    elif stall_knowledge == "Inferred":
        stall_emoji = "🟡"
    else:
        stall_emoji = "🔴"

    print(DIVIDER)
    print("                         DISH SAFETY AUDIT")
    print(DIVIDER)

    print(f"[USERNAME] {username}")
    print("[USER PROFILE & RESTRICTIONS]")
    print_user_restrictions(restrictions)

    print(f"[DISH] {dish}")
    print(f"[LOCATION/STALL] {stall}\n")

    print(f"[STALL STATUS: {stall_knowledge} {stall_emoji}]")
    print("[Stall Insights]")
    print(f"{result_data.get('stall_specific_insights')}\n")

    print(SECTION)
    print_risk_assessment(result_data)
    print_allergy_conflicts(result_data)
    print()
    print_dietary_status(result_data)
    print()
    print_cross_contact_risks(result_data)
    print()

    print_ingredient_breakdown_tree(result_data)

    print(f"\n{DIVIDER}")
    print("⚠️ ADVISORY DISCLAIMER: This tool is advisory only.")
    print("   Always verify with store owners for safety.")
    print(DIVIDER)


# ============================================================
# RESTRICTION INPUT AND MENU
# ============================================================

def parse_restrictions(raw_text):
    """Split comma-separated restrictions into a clean list."""
    items = [
        item.strip().lower()
        for item in raw_text.split(",")
        if item.strip()
    ]
    return items if items else ["none"]


def parse_number_list(raw_text, max_value):
    """Parse selected menu numbers, returning None if invalid."""
    parts = raw_text.replace(",", " ").split()

    if not parts or not all(part.isdigit() for part in parts):
        return None

    numbers = [int(part) for part in parts]

    if any(number < 1 or number > max_value for number in numbers):
        return None

    return numbers


def show_category_menu(menu_entries, selected, custom_items):
    """Display the main category menu."""
    print(f"\n{SECTION}")
    print(" SELECT YOUR ALLERGIES / RESTRICTIONS")
    print(SECTION)

    last_group = None

    for number, (group, title, items) in enumerate(
        menu_entries, start=1
    ):
        if group != last_group:
            print(f"\n  {group.upper()}")
            last_group = group

        ticked = sum(
            1 for item in items if item.lower() in selected
        )
        tag = f" ({ticked} selected)" if ticked else ""
        print(f"    {number}. {title}{tag}")

    custom_number = len(menu_entries) + 1
    ticked_custom = sum(
        1 for item in custom_items if item.lower() in selected
    )
    tag = f" ({ticked_custom} selected)" if ticked_custom else ""

    print("\n  OTHER")
    print(f"    {custom_number}. Other (type your own){tag}")
    print("\n  Enter a number to open it.")
    print("  D = Done    C = Clear everything")
    print(
        f"\nCurrently selected: "
        f"{', '.join(sorted(selected)) if selected else 'none'}"
    )


def run_item_menu(title, items, selected, allow_custom=False):
    """Allow the user to select or deselect items."""
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
    """Display the restriction menu and return selected restrictions."""
    menu_entries = [
        ("Allergies", category, items)
        for category, items in ALLERGEN_CATALOG.items()
    ]
    menu_entries.append(
        ("Restrictions", "Dietary / religious", DIETARY_RESTRICTIONS)
    )

    other_number = len(menu_entries) + 1
    selected = {
        restriction.lower()
        for restriction in (current or [])
        if restriction.lower() != "none"
    }

    custom_items = sorted(
        restriction
        for restriction in selected
        if restriction not in KNOWN_ITEMS
    )

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
            run_item_menu(
                "Other", custom_items, selected, allow_custom=True
            )

        else:
            print("Please enter a number, 'd' or 'c'.")

    return sorted(selected) if selected else ["none"]


# ============================================================
# USER AUTHENTICATION — MERGED VERSION
# ============================================================

def handle_user_authentication():
    """Handle admin login and regular user profile setup."""

    print(f"\n{DIVIDER}")
    print("   HAWKER DIETARY & INGREDIENT SAFETY AUDITOR")
    print(DIVIDER)

    while True:
        username = input("Enter your username: ").strip()

        if username.lower() == "admin":
            if admin_authentication():
                return "Admin", []

            print("Incorrect password.")
            continue

        if username and all(
            char.isalnum() or char in {"_", "-"}
            for char in username
        ):
            username = username.lower()
            break

        print(
            "Invalid username. Use only letters, numbers, "
            "underscores, or hyphens."
        )

    user_profile = get_user_profile(username)

    if user_profile:
        print(f"\nWelcome back, {user_profile['username']}!")
        print(
            "Current saved restrictions: "
            f"{', '.join(user_profile['restrictions'])}"
        )

        if get_yes_no_input(
            "Would you like to update your dietary restrictions? (y/n): "
        ) == "y":
            restrictions = prompt_for_restrictions(
                current=user_profile["restrictions"]
            )
            restrictions = group_restrictions(restrictions)
            save_user_profile(username, restrictions)
            print("Profile updated successfully!")
        else:
            restrictions = user_profile["restrictions"]

    else:
        print(
            f"\nNew user detected ('{username}'). "
            "Let's set up your dietary profile."
        )
        restrictions = prompt_for_restrictions()
        restrictions = group_restrictions(restrictions)
        save_user_profile(username, restrictions)
        print(f"Profile saved successfully for {username}!")

    return username, restrictions


# ============================================================
# ADMIN PROFILE SEARCH — PRESERVED FROM EBAO
# ============================================================

def run_admin_profile_search(username):
    """Allow the admin to search saved user profiles."""
    if username != "Admin":
        return True

    choice = get_yes_no_input(
        "\nSearch user profiles? (y/n): "
    )

    if choice == "n":
        return False

    search_term = input(
        "Enter a username or dietary restriction to search for: "
    ).strip()

    if not search_term:
        print("Search term cannot be blank.")
        return True

    matches = search_user_profiles(search_term)

    if not matches:
        print("No matching user profiles found.")
        return True

    print("\nMatching user profiles:")
    for profile in matches:
        print(
            f"- {profile['username']}: "
            f"{', '.join(profile['restrictions'])}"
        )

    return True


# ============================================================
# STALL AND DISH INPUT
# ============================================================

def get_user_inputs():
    """Prompt the user for the stall and dish to audit."""
    print(f"\n{SECTION}")
    print(" NEW DISH AUDIT")
    print(f"{SECTION}\n")

    stall = input("Enter the stall name/location: ").strip()
    dish = input("Enter the dish name: ").strip()

    return stall, dish

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
# --- AI Error Display Helpers ---
def display_api_key_error():
    print("[AI Manager] GEMINI_API_KEY is not set. Please set it in your .env file.")

def display_attempt_error(attempt, max_tries, error):
    print(f"[AI Manager] Attempt {attempt}/{max_tries} failed: {error}")
