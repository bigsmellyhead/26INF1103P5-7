
from io_manager import IOManager
from ai_manager import AIManager
from logic_manager import LogicManager
from data_manager import DataManager
from UserProfile import UserProfile
from Data import AIAuditData
def main():

    #Initialise all the managers
    data_manager = DataManager()
    logic_manager = LogicManager()
    io_manager = IOManager(data_manager.get_user_profile, data_manager.save_user_profile)
    ai_manager = AIManager(io_manager.display_error)


    # Initialize MySQL database and create missing tables
    data_manager.initialize_database()

    # Authenticate or register user profile
    username, restrictions = io_manager.handle_user_authentication()
    audit_results = []

    while True:
        stall, dish = io_manager.get_user_inputs()

        if not stall or not dish:
            print("Error: Stall and dish names cannot be blank.")
            continue

        try:
            print("\nProcessing audit with AI reasoning engine...")

            # Query LLM API
            ai_output = ai_manager.query_ai_safety_auditor(
                stall, dish, restrictions
            )

            if ai_output is None:
                raise ValueError(
                    "The AI could not complete this audit after several "
                    "tries or the API key is not configured properly."
                )

            # Validate schema and enforce rules
            audit_results.clear()
            processed_data = logic_manager.validate_and_process_logic(
                AIAuditData(
                    UserProfile(
                        username,
                        restrictions
                    ),
                    stall,
                    dish,
                    ai_output
                )
            )

            # Form final log entry
            final_record = processed_data.to_dict()

            # Save audit record to MySQL
            data_manager.append_audit_log(final_record)

            # Display results
            io_manager.display_audit_result(processed_data)

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
