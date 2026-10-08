from io_manager import handle_user_authentication, get_user_inputs, display_audit_result
from logic_manager import validate_and_process_logic
from data_manager import initialize_database, append_audit_log


def main():
    initialize_database()

    # Authenticate or register user profile
    username, restrictions = handle_user_authentication()

    while True:
        stall, dish = get_user_inputs()

        if not stall or not dish:
            print("Error: Stall and dish names cannot be blank.")
            continue

        try:
            print("\nProcessing audit with temporary local reasoning engine...")

            # Temporary replacement for ai_manager
            raw_ai_output = {
                "stall": stall,
                "dish": dish,
                "restrictions": restrictions,
                "safe": True,
                "reason": "Temporary audit result. AI safety auditor not yet connected."
            }

            # Validate schema and enforce rules
            processed_data = validate_and_process_logic(raw_ai_output)

            # Form final log entry
            final_record = {
                "username": username,
                "restrictions": restrictions,
                "stall": stall,
                "dish": dish,
                **processed_data
            }

            # Save to JSON flat file database
            append_audit_log(final_record)

            # Display results
            display_audit_result(
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
