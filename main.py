from io_items.io_manager import IOManager
from ai.ai_manager import AIManager
from logic.logic_manager import LogicManager
from database.data_manager import DataManager
from Data import AIAuditData


class RestrictionDetector:
    """Orchestrates the Hawker Dietary and Ingredient Safety Auditor lifecycle."""
    def __init__(
        self,
        data_manager: DataManager | None = None,
        logic_manager: LogicManager | None = None,
        io_manager: IOManager | None = None,
        ai_manager: AIManager | None = None,
    ) -> None:
        # Support dependency injection while defaulting to standard managers
        self.data_manager = data_manager or DataManager()
        self.logic_manager = logic_manager or LogicManager()
        self.io_manager = io_manager or IOManager(self.data_manager)
        self.ai_manager = ai_manager or AIManager(self.io_manager.display_error)
        self.profile = None

    def _initialize_session(self) -> None:
        """Prepares database tables and authenticates the active user profile."""
        self.data_manager.initialize_database()
        self.profile = self.io_manager.handle_user_authentication()

    def _execute_audit(self, stall: str, dish: str) -> None:
        """Runs a single end-to-end safety audit pipeline for a stall and dish."""
        try:
            print("\nProcessing audit with AI reasoning engine...")
            ai_output = self.ai_manager.query_ai_safety_auditor(
                stall, dish, self.profile
            )

            if ai_output is None:
                raise ValueError(
                    "The AI could not complete this audit after several "
                    "tries or the API key is not configured properly."
                )

            raw_audit = AIAuditData(self.profile, stall, dish, ai_output)
            processed_data = self.logic_manager.validate_and_process_logic(raw_audit)

            self.data_manager.append_audit_log(self.profile, processed_data.to_dict())
            self.io_manager.display_audit_result(processed_data)

        except Exception as e:
            print(f"\n[System Error Caught]: {e}")
            print("Please try your audit request again.")

    def _should_continue(self) -> bool:
        """Prompts the user to decide whether to run another audit."""
        choice = input("Would you like to audit another dish? (y/n): ").strip().lower()
        return choice == "y"

    def run(self) -> None:
        """Starts the main application loop."""
        self._initialize_session()

        while True:
            stall, dish = self.io_manager.get_user_inputs()

            if not stall or not dish:
                print("Error: Stall and dish names cannot be blank.")
                continue

            self._execute_audit(stall, dish)

            if not self._should_continue():
                print("Exiting application. Stay safe!")
                break


if __name__ == "__main__":
    app = RestrictionDetector()
    app.run()