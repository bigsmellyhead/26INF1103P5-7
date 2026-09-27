# io_manager.py
def print_hidden_ingredients_tree(result_data):
    symbol_startTree = "├── "
    symbol_endTree = "└── "

    print("---------------------------------------------------------")
    print("🔍  Trigger Breakdown")
    print("---------------------------------------------------------")
    allergen_list = result_data.get('hidden_ingredients')
    for index, allergen_dict in enumerate(allergen_list):
        if(index == len(allergen_list)-1):
            output = symbol_endTree
            indent = 5 * " "
        else:
            output = symbol_startTree
            indent = "│" + 4 * " "

        for allergen, ingredients in allergen_dict.items():
            print(output+"["+allergen+"]")
            for index,ingredient in enumerate(ingredients):
                
                if(index == len(ingredients)-1):
                    output = indent+symbol_endTree
                else:
                    output = indent+symbol_startTree
                print(output+"["+ingredient+"]")


def display_audit_result(username, stall, dish, restrictions, result_data):

    COLOR_RED = "\033[31m"
    COLOR_RESET= "\033[0m"


    """Displays the final processed audit report clearly to the user."""
    print("=========================================================")
    print("               AUDIT RESULT REPORT            ")
    print("=========================================================")
    print(f"User Profile         : {username} ({', '.join(restrictions)})")
    print(f"Location / Stall     : {stall}")
    print(f"Dish Evaluated       : {dish}\n")

    print("=========================================================")
    print("Risk Assessment:")
    print("=========================================================\n")
    print(f"Risk Score           : {result_data.get('risk_score')}%")
    print(f"Risk Level           : {COLOR_RED}{result_data.get('risk_level')}{COLOR_RESET}")
    safety_status = "SAFE TO EAT" if result_data.get('is_safe') else "NOT SAFE / AVOID"
    print(f"Safety Status        : [{safety_status}]\n")
    
    print(f"Stall Insights: ")
    print(f"{result_data.get('stall_specific_insights')}\n")

    print_hidden_ingredients_tree(result_data)

    print(f"Reasoning:")
    print(f"{result_data.get('reasoning')}\n    ")
    print("----------------------------------------------")
    print("⚠️  ADVISORY DISCLAIMER: This tool is advisory only.")
    print("   Always verify with store owners for safety.")
    print("==============================================\n")