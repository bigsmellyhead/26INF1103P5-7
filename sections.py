from abc import ABC, abstractmethod
from Data import ResultAuditData
from utils import DIVIDER, RISK_COLOR_MAP, SECTION, COLOR_RESET, COLOR_RED, COLOR_GREEN, COLOR_YELLOW
from art import text2art
class ReportSection(ABC):
    @abstractmethod
    def render(self, data: ResultAuditData):
        pass
class HeaderSection(ReportSection):
    def render(self, data: ResultAuditData):
        print(f"{DIVIDER}")
        print("                         DISH SAFETY AUDIT            ")
        print(f"{DIVIDER}")

class UserSummarySection(ReportSection):
    def render(self, data: ResultAuditData):
        """!
        @brief   - Prints the structured summary of a user's allergies, dietary restrictions, and other flags.
        @details - Extracts and sequentially prints to stdout from sub-lists from the parameter 'restrictions' in the following order:
                1. Allergies
                2. Dietary Restrictions
                3. Others
                *Prints 'None' for any empty lists

        @param restrictions - A dictionary containing lists mapping to the keys "allergies", "dietary_restrictions", and "others".
        @return None
        """
        # User and Restrictions section
        print(f"[USERNAME] {data.user_profile.username}")
        print(f"[USER PROFILE & RESTRICTIONS]")

        profile = data.user_profile
        categories = [
            ("allergies", "Allergies"),
            ("dietary_restrictions", "Dietary Restrictions"),
            ("other", "Other")
        ]
        for key, label in categories:
            items = profile.items_in(key)
            if not items:
                print(f"  • {label}: None")
            else:
                print(f"  • {label}:")
                for item in items:
                    # Dietary items have no severity, so only show it when there is one
                    level = profile.severity_label(item)
                    print(f"    - {item} ({level})" if level else f"    - {item}")
        print("")

class StallInsightSection(ReportSection):
    def render(self, data: ResultAuditData):
        # Stall and Insights Section
        stall_knowledge = data.result["stall_knowledge"]
        stall_emoji = "🟢" if stall_knowledge == "Known" else "🟡" if stall_knowledge == "Inferred" else "🔴"
        print(f"[DISH] {data.dish}")
        print(f"[LOCATION/STALL] {data.stall}\n")
        print(f"[STALL STATUS: {stall_knowledge} {stall_emoji}]")
        print(f"[Stall Insights]")
        print(f"{data.result.get('stall_specific_insights')}\n")

class RiskAssessmentSection(ReportSection):
    def render(self, data: ResultAuditData):
        """!
        @brief   -  Evaluates and prints a colored risk assessment statement alongside safety verdicts.
        @details -  Processes execution fields to dynamically evaluate severity thresholds. 
                    It utilizes a Python match-case block to match 'High', 'Medium', or 'Low' text levels to terminal color constants, 
                    then prints a final binary safety verdict ('SAFE TO EAT' vs 'NOT SAFE / AVOID') alongside contextual logic reasoning.

        @param data - A dictionary containing  keys: 'risk_level' (str), 'is_safe' (bool), 'risk_score' (int/float), and 'reasoning' (str).
        @note - Utilizes local ANSI constants (`COLOR_RED`, `COLOR_YELLOW`, `COLOR_GREEN`, `COLOR_RESET`) to output color metrics into the terminal interface.
        @return None
        """
        # ANSI Colour definitions
        #Analyse Risk Score and assign color codes based on risk score
        risk_level = data.result.get('risk_level', "")
        CURRENT_COLOR = RISK_COLOR_MAP.get(risk_level)
        

        safety_status = "SAFE TO EAT" if data.result.get('is_safe') else "NOT SAFE / AVOID"
        #INSERT ASCII ART
        text_to_render = f"Risk Assessment: {data.result.get('risk_score')}% ({risk_level})"
        art = text2art(text_to_render,font = 'small', chr_ignore=True)
        print(f"{CURRENT_COLOR}{art}")
        art_2 = text2art(f"VERDICT: {safety_status}",font = 'small', chr_ignore=True)
        print(art_2)
        print(f"Reasoning:", end = " ")
        print(f"{data.result.get('reasoning')}\n    {COLOR_RESET}")

class AllergyConflictSection(ReportSection):

    def render(self, data: ResultAuditData):
        """!
        @brief   - Prints the Allergen Conflicts to stdout
        @details - Extracts and prints detected allergy conflicts from data. 
                *Prints 'None' if no conflicts are found, or lists each violation.

        @param data - Dictionary containing 'allergy_conflicts' key 
        @return None
        """
        conflicts = data.result.get("allergy_conflicts",[])

        if not conflicts:
            print("🚨 DETECTED CONFLICTS: None")
        else:
            print("🚨 DETECTED CONFLICTS:")
            for conflict in conflicts:
                # Each conflict is a dict; LogicManager added "severity" from the user's profile
                severity = conflict.get("severity", "HIGH")
                color = RISK_COLOR_MAP.get(self._SEVERITY_TO_RISK.get(severity), "")
                print(f"• {color}[{severity}] {conflict.get('restriction')}{COLOR_RESET} "
                      f"({conflict.get('presence', '').lower()}) - {conflict.get('ingredient')}")
        print("")

    # Also uses the Low/Medium/High colours from utils
    _SEVERITY_TO_RISK = {"LOW": "Low", "MED": "Medium", "HIGH": "High"}
        


class DietaryStatusSection(ReportSection):
    def render(self, data: ResultAuditData):
        """!
        @brief   - Prints the Dietary Status to stdout
        @details - Extracts and prints dietary status flags and values from result_data.
                *Prints 'None' if the status is empty, or lists each key-value pair.

        @param data - Dictionary containing 'dietary_status' key
        @return None
        """
        dietary_status = data.result.get("dietary_status",{})
        
        if not dietary_status:
            print("🌿 DIETARY STATUS: None")
        else:
            print("🌿 DIETARY STATUS:")
            for key , value in dietary_status.items():
                print(f"• {key}: {value}")
        print("")
class CrossContactSection(ReportSection):

    def render(self, data: ResultAuditData):
        """!
        @brief   - Prints the Cross-Contamination Risks to stdout
        @details - Extracts and prints cross-contamination risks from data.
                *Prints 'None' if the list is empty, or lists each risk.

        @param data - Dictionary containing 'cross_contact_risks' key
        @return None
        """
        cross_contact_risks = data.result.get("cross_contact_risks",[])
        if not cross_contact_risks:
            print("⚠️  Cross-Contamination Risks: None")
        else:
            print("⚠️  Cross-Contamination Risks:")
            for risk in cross_contact_risks:
                print(f"• [ENVIRONMENTAL RISK] {risk}")
        print("")


class IngredientBreakdownSection(ReportSection):
    def render(self, data: ResultAuditData):   
        """!
        @brief   - Prints the full ingredient breakdown and traceability tree to stdout
        @details - Checks for valid result data, prints the section header, extracts the root 
                dish name from the 'ingredient_tree', and initiates the recursive 
                child tree printing function.

        @param result_data - Dictionary containing the 'ingredient_tree' key mapping to the root node.
        @return None
        """


        print(f"{SECTION}")
        print("🌳 FULL INGREDIENT BREAKDOWN & TRACEABILITY:")
        print(f"{SECTION}")
        ingredient_list = data.result.get("ingredient_tree")
        if not ingredient_list:
            return

        print(f"Dish: {ingredient_list['name']}")
        self._print_children_tree(ingredient_list, "")

    def _has_triggered_descendant(self, node):
        if node.get("conflict") and node.get("status") == "Trigger":
            return True
        for child in node.get("children", []):
            if self._has_triggered_descendant(child):
                return True
        return False

    """!
        @brief   - Recursively prints the child nodes of an ingredient tree with structural tree lines
        @details - Iterates through the children of a starting node, checks their status and 
                conflict state to apply color formatting, and recursively processes nested 
                sub-children with proper indentation and tree branching symbols (├── and └──).
    
        @param starting_node - Dictionary representing the current node (contains 'name', 'status', 'conflict', and optionally 'children').
        @param prefix        - String used for tracking recursive indentation and tree alignment.
        @return None
        """
    def _print_children_tree(self, starting_node, prefix = ""):
        children = starting_node.get("children", [])

        symbol_startTree = "├── "
        symbol_endTree = "└── "
        indentation = ""
        #Loop through the children
        for index, child in enumerate(children):
            child_name = child.get("name")
            child_status = child.get("status")
            child_conflict = child.get("conflict")
            child_verdict = ""

            # Factor in whether the node itself has a conflict or has triggered descendants
            if child_status == "Trigger" and (child_conflict or self._has_triggered_descendant(child)):
                if child_conflict:
                    child_verdict = f"{COLOR_RED}<-----[{child_status}: {child_conflict}]{COLOR_RESET}"
                else:
                    child_verdict = f"{COLOR_RED}({child_status}){COLOR_RESET}"
            else:
                child_verdict = f"{COLOR_GREEN}({child_status}){COLOR_RESET}"

            if(index == len(children) - 1):
                print(f"{prefix}{symbol_endTree}{child_name} {child_verdict}")
                indentation = "    "
            else:
                print(f"{prefix}{symbol_startTree}{child_name} {child_verdict}")
                indentation = "│   "

            # Show the stall-specific note under the ingredient it applies to
            child_insight = child.get("stall_insight")
            if child_insight:
                print(f"{prefix}{indentation}↳ {COLOR_YELLOW}Stall: {child_insight}{COLOR_RESET}")
                
            if("children" in child):
                self._print_children_tree(child, prefix + indentation)

# prints why the rules changed or questioned the AI's verdict (score got raised or capped)
class FlagsSection(ReportSection):
    def render(self, data: ResultAuditData):
        flags = data.result.get("flags", [])
        if not flags:
            return
        print(f"\n🔎 SAFETY RULE NOTES:")
        for flag in flags:
            print(f"• {flag}")

class DisclaimerSection(ReportSection):
    def render(self, data: ResultAuditData):
        print(f"\n{DIVIDER}")
        print("⚠️  ADVISORY DISCLAIMER: This tool is advisory only.")
        print("   Always verify with store owners for safety.")
        print(f"{DIVIDER}")