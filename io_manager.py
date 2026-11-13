# io_manager.py
from allergen_catalog import group_restrictions
from restriction_menu import RestrictionMenu
import utils
from art import text2art
from allergen_catalog import create_restriction
from collections.abc import Callable
from Data import ResultAuditData
from allergen_catalog import create_restriction, needs_severity, SEVERITY_DESCRIPTIONS
from audit_report_renderer import AuditReportRenderer
from sections import (HeaderSection, UserSummarySection, StallInsightSection, RiskAssessmentSection, 
AllergyConflictSection, DietaryStatusSection, CrossContactSection, IngredientBreakdownSection, DisclaimerSection)


class IOManager:

    __load_data : Callable
    __save_data : Callable
    # Composes a audit renderer that helps to render all sections
    __audit_renderer: AuditReportRenderer

    def __init__(self, load_data: Callable, save_data: Callable):
        self.__load_data = load_data
        self.__save_data = save_data
        self.__audit_renderer = AuditReportRenderer(
            [
                HeaderSection(),
                UserSummarySection(),
                StallInsightSection(),
                RiskAssessmentSection(),
                AllergyConflictSection(),
                DietaryStatusSection(),
                CrossContactSection(),
                IngredientBreakdownSection(),
                DisclaimerSection()
            ]
        )

    # ================= Restriction Menu (display + input only) =================

    def show_category_menu(self, menu: RestrictionMenu):
        # --- Level 1: Allergies first, then Restrictions, then Other ---
        print(f"\n{utils.SECTION}")
        print(" SELECT YOUR ALLERGIES / RESTRICTIONS")
        print(utils.SECTION)

        last_group = None
        for number, (group, title, items) in enumerate(menu.entries, start=1):
            # Print a group header (ALLERGIES / RESTRICTIONS) whenever the group changes
            if group != last_group:
                print(f"\n  {group.upper()}")
                last_group = group

            ticked = menu.count_selected(items)
            tag = f"  ({ticked} selected)" if ticked else ""
            print(f"    {number}. {title}{tag}")

        ticked_custom = menu.count_selected(menu.custom_items)
        tag = f"  ({ticked_custom} selected)" if ticked_custom else ""
        print("\n  OTHER")
        print(f"    {menu.other_number}. Other (type your own){tag}")

        print("\n  Enter a number to open it.")
        print("  D = Done    C = Clear everything")
        print(f"\nCurrently selected: {', '.join(menu.selected_names()) or 'none'}")

    def run_item_menu(self, menu: RestrictionMenu, title, items, allow_custom=False):
        # --- Level 2: tick / untick specific allergens inside one category ---
        # The menu object remembers what is ticked. This method only draws and reads the answer.
        while True:
            print(f"\n{utils.SECTION}")
            print(f" {title}")
            print(utils.SECTION)

            if not items:
                print("  (nothing here yet)")
            for number, item in enumerate(items, start=1):
                mark = "x" if menu.is_selected(item) else " "
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
                menu.select_all(items)
            elif choice == "n":
                menu.select_none(items)
            elif choice == "t" and allow_custom:
                menu.add_custom(input(utils.CUSTOM_PROMPT))
            else:
                numbers = menu.parse_numbers(choice, len(items))
                if numbers is None:
                    print("Invalid choice. Please try again.")
                    continue
                menu.toggle(items, numbers)

    def prompt_for_restrictions(self, current=None):
        # --- Prompts the user for Restrictions via the category menu and Returns them ---
        """Walks the user through the allergen menu. Returns a clean list, or ['none']."""
        menu = RestrictionMenu(current)

        while True:
            self.show_category_menu(menu)
            choice = input("Your choice: ").strip().lower()

            if choice == "d":
                break
            elif choice == "c":
                menu.clear()
            elif choice.isdigit() and 1 <= int(choice) <= len(menu.entries):
                group, title, items = menu.entries[int(choice) - 1]
                self.run_item_menu(menu, f"{group} > {title}", items)
            elif choice.isdigit() and int(choice) == menu.other_number:
                self.run_item_menu(menu, "Other", menu.custom_items, allow_custom=True)
            else:
                print("Please enter a number, 'd' or 'c'.")

        return menu.selected_names() or ["none"]

    def flatten_restrictions(self, restrictions):
        if isinstance(restrictions, dict):
            return [item for key in ("allergies", "dietary_restrictions", "other")for item in restrictions.get(key, [])]
        return [item for item in restrictions if item != "none"]

    # Input handling for user authentication
    def handle_user_authentication(self):
        """Handles existing user check, profile editing, or new user registration."""

        # --- App banner ---
        print(f"\n{utils.DIVIDER}")
        print("   HAWKER DIETARY & INGREDIENT SAFETY AUDITOR")
        print(f"{utils.DIVIDER}\n")

        # --- Get and validate username ---
        username = input("Enter your username: ").strip()

        if not username:
            # Fall back to a default rather than letting an empty username through
            print("\nUsername cannot be empty. Defaulting to 'guest'.")
            username = "guest"

        # Look up this username in the saved profiles (returns None if new)
        user_profile = self.__load_data(username)

        if user_profile:
            # --- Existing user: show their saved data ---
            saved_names = self.flatten_restrictions(user_profile['restrictions'])
            print(f"\nWelcome back, {user_profile['username']}!")
            print(f"Current saved restrictions: {', '.join(saved_names) or 'none'}\n")

            # Loop until the user gives a valid y/n answer
            while True:
                update_choice = input("Would you like to update your dietary restrictions? (y/n): ").strip().lower()
                if update_choice in ['y', 'n']:
                    break
                print("Please enter only 'y' or 'n'.")

            if update_choice == 'y':
                # --- User wants to change their restrictions (menu opens pre-ticked) ---
                names = self.prompt_for_restrictions(current=saved_names)
                severity = self.prompt_for_severity(names, current=user_profile['restrictions'].get("severity", {}))
                self.print_severity_summary(self.build_restrictions(names, severity)) # This is to print Severity Summary

                # Overwrite the profile in the JSON database
                restrictions = group_restrictions(names, severity)
                self.__save_data(username, restrictions)

                saved = [n for n in names if n != "none"]
                print(f"\nProfile updated! Saved {len(saved)} restriction(s): {', '.join(saved) or 'none'}")
            else:
                # --- User declined to update: keep existing restrictions as-is ---
                print("No updates made.")
                restrictions = user_profile['restrictions']
        else:
            # --- New user: walk them through initial setup ---
            print(f"\nNew user detected ('{username}'). Let's set up your dietary profile.")
            names = self.prompt_for_restrictions()
            severity = self.prompt_for_severity(names)
            self.print_severity_summary(self.build_restrictions(names, severity)) # This is to print Severity Summary

            # Create the profile for the first time
            # Reformat the restrictions to group them according:
            # Allergens
            # Dietary Restrictions
            # Others
            restrictions = group_restrictions(names, severity)

            ## Save to database
            self.__save_data(username, restrictions)
            saved = [n for n in names if n != "none"]
            print(f"\nProfile saved for {username}! Saved {len(saved)} restriction(s): {', '.join(saved) or 'none'}")

        # Hand back the username and their current (possibly just-updated) restrictions
        return username, restrictions

    # Input handling for stall and dish
    def get_user_inputs(self):
        """Prompts the user for the stall and dish they want to audit."""
        # --- Audit section header ---
        print(f"\n{utils.SECTION}")
        print(" NEW DISH AUDIT")
        print(f"{utils.SECTION}\n")

        # --- Collect the two pieces of info needed to run the audit ---
        stall = input("Enter Hawker Centre or Stall Name (e.g., Maxwell Food Centre): ").strip()
        dish = input("Enter Dish Name (e.g., Chicken Rice): ").strip()

        return stall, dish

    # --- AI Error Display Helpers ---
    def display_error(self, data : str):
        #print("[AI Manager] GEMINI_API_KEY is not set. Please set it in your .env file.")
        print(data)

    """!
    @brief   - Displays the final processed audit report clearly to the user
    @details - Compiles and prints a comprehensive dish safety audit to stdout. 
            This includes user profile/restrictions, stall details, knowledge status, 
            risk assessment, allergy conflicts, dietary status, cross-contamination 
            risks, and the full ingredient breakdown tree, followed by an advisory disclaimer.

    @param data  - A resultaudit data containing audit results (stall knowledge, insights, conflicts, tree, etc.).
    @return None
    """
    def display_audit_result(self, data: ResultAuditData):
        """Displays the final processed audit report clearly to the user."""
        self.__audit_renderer.render_sections(data)

    def prompt_for_severity(self, names, current=None): #Prompt for Severity Section
            current = current or {}
            severity = {}

            already_rated = [name for name in names if needs_severity(name) and name in current]
            change_saved = False
            if already_rated:
                print(f"\nYou already have severity level saved for: {', '.join(already_rated)}")
                while True:
                    answer = input("Would you like to change any of them? (y/n): ").strip().lower()
                    if answer in ['y', 'n']:
                        break
                    print("Please enter only 'y or 'n'.")
                change_saved = (answer == 'y')

            for name in names: #name means the Allergy name itself
                if not needs_severity(name):
                    continue
                previous = current.get(name)

                if previous and not change_saved:
                    severity[name] = previous
                    continue

                print(f"\nHow severely does ({name}) affect you?")
                for number, (level, text) in enumerate(SEVERITY_DESCRIPTIONS.items(), start=1):
                    print(f"    {number}. {level:<4} - {text}")
                hint = f"   (Enter = keep {previous})" if previous else ""
                while True:
                    choice = input(f"Your choice 1-3{hint}: ").strip().upper()
                    if not choice and previous:
                        severity[name] = previous
                        break
                    if choice in utils.SEVERITY_ANSWERS:
                        severity[name] = utils.SEVERITY_ANSWERS[choice] #choice is the user's choice - 1-3, low,med,high
                        break
                    print("Please enter 1,2 or 3.")
            return severity    
    
    def build_restrictions(self, names, severity): #Takes the list of ticked names and turn each one into a restriction object, turning them into a set.
        return {create_restriction(n, severity.get(n)) for n in names if n != "none"}

    def print_severity_summary(self, restrictions): #Check every item passes the check and prints the severity line
        for r in sorted(restrictions, key=lambda r: r.name):
            level = getattr(r, "severity_level", None)
            if level:
                print(f"Severity for ({r.name}): {level.title()}")

