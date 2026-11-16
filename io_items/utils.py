DIVIDER = "=" * 100
SECTION = "-" * 100
# ANSI Colour definitions
COLOR_RED = "\033[31m"
COLOR_YELLOW = "\033[33m"
COLOR_GREEN = "\033[32m"
COLOR_RESET= "\033[0m"

CUSTOM_PROMPT = (
    # --- Prompt for anything not in the catalog ---
    "Type your own allergies/restrictions, separated by commas\n"
    "(e.g. g6pd, blue berries): ")

SEVERITY_ANSWERS = {"1": "LOW", "L": "LOW", "LOW": "LOW",
                    "2": "MED", "M": "MED", "MED": "MED",
                    "3": "HIGH", "H": "HIGH", "HIGH": "HIGH"}

RISK_COLOR_MAP = {
    'High': COLOR_RED,
    'Medium': COLOR_YELLOW,
    'Low': COLOR_GREEN,

}