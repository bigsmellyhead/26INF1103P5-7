import pytest
from unittest.mock import Mock

import io_manager as io


# --------------------------------------------------
# Helper data
# --------------------------------------------------

def make_result(**overrides):
    """Create a typical AI audit result for display tests."""
    result = {
        "stall_knowledge": "Known",
        "stall_specific_insights": "The stall uses a shared cooking area.",
        "risk_level": "Low",
        "is_safe": True,
        "risk_score": 10,
        "reasoning": "No known conflicts were detected.",
        "allergy_conflicts": [],
        "dietary_status": {},
        "cross_contact_risks": [],
        "ingredient_tree": {
            "name": "Chicken Rice",
            "status": "Safe",
            "conflict": None,
            "children": [
                {
                    "name": "Chicken",
                    "status": "Safe",
                    "conflict": None,
                    "children": [],
                }
            ],
        },
    }
    result.update(overrides)
    return result


# --------------------------------------------------
# parse_restrictions()
# --------------------------------------------------

@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Egg", ["egg"]),
        ("Egg, Milk", ["egg", "milk"]),
        (" Egg , MILK ", ["egg", "milk"]),
        ("egg,,milk,", ["egg", "milk"]),
        ("", ["none"]),
        ("   ", ["none"]),
        (" , , ", ["none"]),
        ("Blue Berries", ["blue berries"]),
    ],
)
def test_parse_restrictions(raw, expected):
    assert io.parse_restrictions(raw) == expected


