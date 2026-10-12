# main.py
from io_manager import handle_user_authentication, run_admin_profile_search, get_user_inputs, display_audit_result, get_yes_no_input
from ai_manager import query_ai_safety_auditor
from logic_manager import validate_and_process_logic
from data_manager import initialize_database, append_audit_log

def main():
    initialize_database()

    # Authenticate Admin or register user profile
       username, restrictions = handle_user_authentication()
       run_admin_profile_search(username)
       if username == "Admin":
           print("\nDatabase search concluded. See you next time!")
           return

    while True:
        stall, dish = get_user_inputs()

        if not stall or not dish:
            print("Error: Stall and dish names cannot be blank.")
            continue

        try:
            print("\nProcessing audit with temporary local reasoning engine...")

             # Query LLM API
            ai_output = query_ai_safety_auditor(stall, dish, restrictions)

            # The AI manager returns None after all its tries fail
            if ai_output is None:
                raise ValueError("The AI could not complete this audit after several tries.")

            # Validate schema and enforce rules
            processed_data = validate_and_process_logic(ai_output, restrictions)

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