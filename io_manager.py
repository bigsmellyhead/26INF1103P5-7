# io_manager.py

from os import name

from psutil import users
from pwinput import pwinput
from data_manager import DataManager
from allergen_catalog import ALLERGEN_CATALOG, DIETARY_RESTRICTIONS, KNOWN_ITEMS , group_restrictions
from database.database import SessionLocal 
from database.models import AuditLog, User
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

    def __init__(self, load_data: Callable, save_data: Callable, data_manager: DataManager):
        self.__load_data = load_data
        self.__save_data = save_data
        self.__data_manager = data_manager
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

    # Admin account settings
    # Change values to what we require, for demo purpose only
    ADMIN_USERNAME = "ADMIN"
    ADMIN_PASSWORD = "Admin123"

    @staticmethod
    def is_admin_username(username):
        """Return True when the supplied username is the admin username."""
        return username == IOManager.ADMIN_USERNAME

    # retrieve input for user profile search
    def _search_user_profiles(self):
        """Find user profiles by username."""
        name = input("Enter username to search: ").strip()

        if not name:
            print("Username cannot be blank.")
            return

        users = self.__data_manager.search_user_profiles(name)

        if not users:
            print("No matching user profiles found.")
            return

        for user in users:
            self._display_profile(user)

    # retrieve input for dietary restriction search
    def _search_dietary_restriction(self):
        """Find user profiles containing a restriction keyword."""
        term = input("Enter a restriction keyword to search for: ").strip()

        if not term:
            print("Restriction keyword cannot be blank.")
            return

        matches = self.__data_manager.search_dietary_restriction(term)

        if not matches:
            print("No profiles found with that restriction keyword.")
            return

        for user in matches:
            self._display_profile(user)

    
    # display a user profile's details
    def _display_profile(self, user):
        """Display a user profile's details."""
        print(f"\nUsername: {user.username}")

        restrictions = user.restrictions or {}

        for category in ("allergies", "dietary_restrictions", "other"):
            items = restrictions.get(category, [])

            if isinstance(items, str):
                items = [items]

            if not isinstance(items, (list, tuple, set)):
                items = []

            items = [
                item for item in items
                if isinstance(item, str) and item.strip()
            ]

            print(
                f"  {category.replace('_', ' ').title()}: "
                f"{', '.join(items) or 'none'}"
            )

    # Get category selection
    def _get_audit_filter_input(self):
        """Ask the admin which restrictions to filter audit history by."""

        selected_items = self.prompt_for_restrictions()

        if not selected_items or selected_items == ["none"]:
            print("No restrictions selected.")
            return None

        return selected_items


	# Coordinate filter audit history by restriction category
    def _filter_audit_history_by_allergy(self):
        """Filter audit history using the admin's selected category."""
        selected_items = self._get_audit_filter_input()

        # Escape if no restrictions were selected
        if selected_items is None:
            return
        
        matches = self.__data_manager.filter_audit_history_by_restrictions(selected_items)
        
        self._display_filtered_audit_history(matches, selected_items)

    # Output filtered audit history 
    def _display_filtered_audit_history(self, matches, selected_category):
        """Display audit records matching the selected restrictions."""

        if not matches:
            print(
                f"No audit history found for: {selected_category}."
            )
            return

        print(f"\nAudit history for: {selected_category}")

        for audit, user in matches:
            print(
                f"\nDate: {audit.created_at}"
                f"\nUsername: {user.username}"
                f"\nStall: {audit.stall or 'Unknown stall'}"
                f"\nDish: {audit.dish or 'Unknown dish'}"
                f"\nSafe: {audit.is_safe}"
                f"\nRisk: {audit.risk_level or 'Unknown'}"
            )
    
    def _run_admin_menu(self):
        """Display the admin menu until the admin chooses to exit."""
        print("\nWelcome, Admin!")

        while True:
            print(
                "\nADMIN MENU\n"
                "1. Search for a user profile\n"
                "2. Search profiles by restriction keyword\n"
                "3. Filter audit history by restriction category\n"
                "4. Exit admin menu"
            )

            choice = input("Select an option: ").strip()

            if choice == "1":
                self._search_user_profiles()
            elif choice == "2":
                self._search_dietary_restriction()
            elif choice == "3":
                self._filter_audit_history_by_allergy()
            elif choice == "4":
                print("Exiting admin menu. Stay safe!")
                return
            else:
                print("Please choose an option from 1 to 4.")

    def run_admin_login(self):
        """Ask for the admin password and open the admin menu if correct."""
        if pwinput("Enter admin password: ", mask="*") != self.ADMIN_PASSWORD:
            print("Invalid admin password. Access denied.")
            return

        self._run_admin_menu()

    # Input handling for restrictions
    def parse_restrictions(self, raw_text):
        # --- Spliting of Allergies / Restrictions by commas "," ---
        """Split comma-separated input into a clean list. Returns ['none'] if empty."""
        items = [r.strip().lower() for r in raw_text.split(",") if r.strip()]
        return items if items else ["none"]

    def parse_number_list(self, raw_text, max_value):
        # --- Turns "1, 3 4" into [1, 3, 4]. Returns None if anything is invalid ---
        parts = raw_text.replace(",", " ").split()
        if not parts or not all(p.isdigit() for p in parts):
            return None
        numbers = [int(p) for p in parts]
        if any(n < 1 or n > max_value for n in numbers):
            return None
        return numbers

    def show_category_menu(self, menu_entries, selected, custom_items):
        # --- Level 1: Allergies first, then Restrictions, then Other ---
        # menu_entries is a list of (group, title, items) tuples
        print(f"\n{utils.SECTION}")
        print(" SELECT YOUR ALLERGIES / RESTRICTIONS")
        print(utils.SECTION)

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

    def run_item_menu(self, title, items, selected, allow_custom=False):
        # --- Level 2: tick / untick specific allergens inside one category ---
        # `selected` (a set) and `items` (a list) are edited in place.
        while True:
            print(f"\n{utils.SECTION}")
            print(f" {title}")
            print(utils.SECTION)

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
                raw = input(utils.CUSTOM_PROMPT)
                for new_item in self.parse_restrictions(raw):
                    if new_item == "none":
                        continue
                    if new_item not in items:
                        items.append(new_item)
                    selected.add(new_item)
            else:
                numbers = self.parse_number_list(choice, len(items))
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

    def prompt_for_restrictions(self, current=None):
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
            self.show_category_menu(menu_entries, selected, custom_items)
            choice = input("Your choice: ").strip().lower()

            if choice == "d":
                break
            elif choice == "c":
                selected.clear()
            elif choice.isdigit() and 1 <= int(choice) <= len(menu_entries):
                group, title, items = menu_entries[int(choice) - 1]
                self.run_item_menu(f"{group} > {title}", items, selected)
            elif choice.isdigit() and int(choice) == other_number:
                self.run_item_menu("Other", custom_items, selected, allow_custom=True)
            else:
                print("Please enter a number, 'd' or 'c'.")

        return sorted(selected) if selected else ["none"]

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

        if self.is_admin_username(username):
            self.run_admin_login()
            return self.handle_user_authentication()  # Restart the process after admin menu

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
                restrictions = group_restrictions(names)
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
            for name in names: #name means the Allergy name itself
                if not needs_severity(name):
                    continue
                previous = current.get(name)
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


