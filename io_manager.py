# io_manager.py

from pwinput import pwinput
from data_manager import DataManager
from restriction_menu import RestrictionMenu
import utils
from collections.abc import Callable
from Data import ResultAuditData
from UserProfile import UserProfile
from allergen_catalog import create_restriction, needs_severity, SEVERITY_DESCRIPTIONS
from audit_report_renderer import AuditReportRenderer
from sections import (HeaderSection, UserSummarySection, StallInsightSection, RiskAssessmentSection,
AllergyConflictSection, DietaryStatusSection, CrossContactSection, IngredientBreakdownSection,
FlagsSection, DisclaimerSection)


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
                FlagsSection(),
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

        for profile in users:
            self._display_profile(profile)

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

        for profile in matches:
            self._display_profile(profile)

    # display a user profile's details (the serializer already cleaned the data)
    def _display_profile(self, profile: UserProfile):
        """Display a user profile's details, with severity where saved."""
        print(f"\nUsername: {profile.username}")

        for category in UserProfile.CATEGORIES:
            items = []
            for item in profile.items_in(category):
                level = profile.severity_label(item)
                items.append(f"{item} ({level})" if level else item)

            print(f"  {category.replace('_', ' ').title()}: {', '.join(items) or 'none'}")

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

    def _edit_restrictions(self, profile: UserProfile) -> None:
        """Run the menus, then update the SAME profile object in place and save it."""
        names = self.prompt_for_restrictions(current=profile.all_restriction_names() or None)
        severity = self.prompt_for_severity(names, current=profile.severity_map())

        # build_restrictions -> set of Restriction objects (AllergenRestriction etc.)
        restrictions = self.build_restrictions(names, severity)
        self.print_severity_summary(restrictions)
        profile.set_restrictions(restrictions)

        # Only now is the profile turned back into a dict (inside DataManager, by the serializer)
        self.__save_data(profile)

    # Input handling for user authentication
    def handle_user_authentication(self) -> UserProfile:
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

        # Look up this username (DataManager returns a UserProfile, or None if new)
        profile = self.__load_data(username)

        if profile:
            # --- Existing user: show their saved data ---
            saved_names = profile.all_restriction_names()
            print(f"\nWelcome back, {profile.username}!")
            print(f"Current saved restrictions: {', '.join(saved_names) or 'none'}\n")

            # Loop until the user gives a valid y/n answer
            while True:
                update_choice = input("Would you like to update your dietary restrictions? (y/n): ").strip().lower()
                if update_choice in ['y', 'n']:
                    break
                print("Please enter only 'y' or 'n'.")

            if update_choice == 'y':
                # --- User wants to change their restrictions (menu opens pre-ticked) ---
                self._edit_restrictions(profile)
                saved = profile.all_restriction_names()
                print(f"\nProfile updated! Saved {len(saved)} restriction(s): {', '.join(saved) or 'none'}")
            else:
                print("No updates made.")
        else:
            # --- New user: start with an empty profile, then fill it in ---
            print(f"\nNew user detected ('{username}'). Let's set up your dietary profile.")
            profile = UserProfile(username)
            self._edit_restrictions(profile)
            saved = profile.all_restriction_names()
            print(f"\nProfile saved for {username}! Saved {len(saved)} restriction(s): {', '.join(saved) or 'none'}")

        # Hand back the profile object itself; everyone else reads from it
        return profile

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
                print("Please enter only 'y' or 'n'.")
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


