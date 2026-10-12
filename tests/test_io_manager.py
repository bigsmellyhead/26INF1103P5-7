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


# --------------------------------------------------
# parse_number_list()
# --------------------------------------------------

@pytest.mark.parametrize(
    "raw, maximum, expected",
    [
        ("1", 5, [1]),
        ("1,3", 5, [1, 3]),
        ("1 3", 5, [1, 3]),
        ("1, 3 4", 5, [1, 3, 4]),
        (" 2 , 4 ", 5, [2, 4]),
        ("1,1", 5, [1, 1]),
        ("", 5, None),
        ("   ", 5, None),
        ("abc", 5, None),
        ("1,x", 5, None),
        ("0", 5, None),
        ("6", 5, None),
        ("1,-2", 5, None),
        ("1.5", 5, None),
        ("1,,2", 5, [1, 2]),
    ],
)
def test_parse_number_list(raw, maximum, expected):
    assert io.parse_number_list(raw, maximum) == expected

# --------------------------------------------------
# print_user_restrictions()
# --------------------------------------------------

def test_print_user_restrictions(capsys):
    io.print_user_restrictions({
        "allergies": ["egg", "peanut"],
        "dietary_restrictions": ["vegetarian"],
        "others": ["g6pd"],
    })

    output = capsys.readouterr().out

    assert "Allergies" in output
    assert "egg" in output
    assert "peanut" in output
    assert "Dietary Restrictions" in output
    assert "vegetarian" in output
    assert "Others" in output
    assert "g6pd" in output


def test_print_user_restrictions_empty_lists(capsys):
    io.print_user_restrictions({
        "allergies": [],
        "dietary_restrictions": [],
        "others": [],
    })

    output = capsys.readouterr().out

    assert "Allergies: None" in output
    assert "Dietary Restrictions: None" in output
    assert "Others: None" in output


def test_print_user_restrictions_missing_keys(capsys):
    io.print_user_restrictions({})

    output = capsys.readouterr().out

    assert "Allergies: None" in output
    assert "Dietary Restrictions: None" in output
    assert "Others: None" in output

