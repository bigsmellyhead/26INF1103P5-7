
from io_manager import IOManager
from ai_manager import AIManager
from logic_manager import LogicManager
from data_manager import initialize_database, append_audit_log
from EventBus import event_bus
from EventName import EventName
from Data import ValidateProcessData

def main():

    #Initialise all the managers
    ai_manager = AIManager(event_bus)

    # event bus subscribes to VALIDATEPROCESSDATA in its constructor but not called directly; G7 PLEASE DO NOT DELETE - josh
    LogicManager(event_bus)

    io_manager = IOManager()


    # Initialize MySQL database and create missing tables
    initialize_database()

    # Authenticate or register user profile
    username, restrictions = io_manager.handle_user_authentication()
    audit_results = []
    event_bus.subscribe_event(EventName.AUDITRESULTDATA, audit_results.append)

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

            while event_bus.active_events:
                event_bus.update()

            if ai_output is None:
                raise ValueError(
                    "The AI could not complete this audit after several "
                    "tries or the API key is not configured properly."
                )

            # Validate schema and enforce rules
            audit_results.clear()
            event_bus.raise_event(
                EventName.VALIDATEPROCESSDATA,
                ValidateProcessData(ai_output, restrictions, username, stall, dish)
            )

            # Logic manager raises AUDITRESULTDATA then delivered to audit_results
            # Update until the bus has no more queued events left
            while event_bus.active_events:
                event_bus.update()   

            processed_data = audit_results.pop().result

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
