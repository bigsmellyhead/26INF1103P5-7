
from io_manager import IOManager
from ai_manager import query_ai_safety_auditor
from logic_manager import validate_and_process_logic
from data_manager import initialize_database, append_audit_log
from EventBus import event_bus
from EventName import EventName
import time
from Data import AttemptErrorData, APIKeyErrorData

def main():
    #Initialise all the managers
    io_manager = IOManager()
    # Initialize MySQL database and create missing tables
    initialize_database()

    # Authenticate or register user profile
    username, restrictions = io_manager.handle_user_authentication()

    while True:
        stall, dish = io_manager.get_user_inputs()

        if not stall or not dish:
            print("Error: Stall and dish names cannot be blank.")
            continue

        try:
            print("\nProcessing audit with AI reasoning engine...")

            # Query LLM API
            ai_output = query_ai_safety_auditor(
                stall, dish, restrictions
            )

            if ai_output is None:
                raise ValueError(
                    "The AI could not complete this audit after several "
                    "tries or the API key is not configured properly."
                )

            # Validate schema and enforce rules
            processed_data = validate_and_process_logic(
                ai_output, restrictions
            )

            # Form final log entry
            final_record = {
                "username": username,
                "restrictions": restrictions,
                "stall": stall,
                "dish": dish,
                **processed_data
            }

            # Save audit record to MySQL
            append_audit_log(final_record)

            # Display results
            io_manager.display_audit_result(
                username,
                stall,
                dish,
                restrictions,
                processed_data
            )

        except Exception as e:
            print(f"\n[System Error Caught]: {e}")
            print("Please try your audit request again.")

        cont = input(
            "Would you like to audit another dish? (y/n): "
        ).strip().lower()

        if cont != "y":
            print("Exiting application. Stay safe!")
            break


if __name__ == "__main__":
    main()