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


# --------------------------------------------------
# print_risk_assessment()
# --------------------------------------------------

@pytest.mark.parametrize(
    "level, color",
    [
        ("High", io.COLOR_RED),
        ("Medium", io.COLOR_YELLOW),
        ("Low", io.COLOR_GREEN),
    ],
)
def test_print_risk_assessment_uses_correct_color(
    level, color, capsys
):
    io.print_risk_assessment({
        "risk_level": level,
        "is_safe": False,
        "risk_score": 85,
        "reasoning": "A conflicting ingredient was detected.",
    })

    output = capsys.readouterr().out

    assert color in output
    assert f"85% ({level})" in output
    assert "NOT SAFE / AVOID" in output
    assert "A conflicting ingredient was detected." in output
    assert io.COLOR_RESET in output


def test_print_risk_assessment_safe_verdict(capsys):
    io.print_risk_assessment({
        "risk_level": "Low",
        "is_safe": True,
        "risk_score": 0,
        "reasoning": "No known conflicts.",
    })

    output = capsys.readouterr().out

    assert "SAFE TO EAT" in output
    assert "NOT SAFE / AVOID" not in output


def test_print_risk_assessment_unknown_level(capsys):
    io.print_risk_assessment({
        "risk_level": "Unknown",
        "is_safe": False,
        "risk_score": 50,
        "reasoning": "Insufficient information.",
    })

    output = capsys.readouterr().out

    assert "Risk Assessment: 50% (Unknown)" in output
    assert "NOT SAFE / AVOID" in output


# --------------------------------------------------
# print_allergy_conflicts()
# --------------------------------------------------

def test_print_allergy_conflicts_empty(capsys):
    io.print_allergy_conflicts({"allergy_conflicts": []})

    output = capsys.readouterr().out

    assert "DETECTED CONFLICTS: None" in output


def test_print_allergy_conflicts_multiple(capsys):
    io.print_allergy_conflicts({
        "allergy_conflicts": ["Peanut", "Milk"],
    })

    output = capsys.readouterr().out

    assert "DETECTED CONFLICTS:" in output
    assert "Peanut" in output
    assert "Milk" in output
    assert output.count("[ALLERGY VIOLATION]") == 2


def test_print_allergy_conflicts_missing_key(capsys):
    io.print_allergy_conflicts({})

    assert "DETECTED CONFLICTS: None" in capsys.readouterr().out
# --------------------------------------------------
# print_dietary_status()
# --------------------------------------------------

def test_print_dietary_status_empty(capsys):
    io.print_dietary_status({"dietary_status": {}})

    assert "DIETARY STATUS: None" in capsys.readouterr().out


def test_print_dietary_status_values(capsys):
    io.print_dietary_status({
        "dietary_status": {
            "Vegetarian": "Not suitable",
            "Halal": "Unknown",
        }
    })

    output = capsys.readouterr().out

    assert "Vegetarian: Not suitable" in output
    assert "Halal: Unknown" in output


def test_print_dietary_status_missing_key(capsys):
    io.print_dietary_status({})

    assert "DIETARY STATUS: None" in capsys.readouterr().out


# --------------------------------------------------
# print_cross_contact_risks()
# --------------------------------------------------

def test_print_cross_contact_risks_empty(capsys):
    io.print_cross_contact_risks({"cross_contact_risks": []})

    assert "Cross-Contamination Risks: None" in (
        capsys.readouterr().out
    )


def test_print_cross_contact_risks_multiple(capsys):
    io.print_cross_contact_risks({
        "cross_contact_risks": [
            "Shared fryer",
            "Shared utensils",
        ]
    })

    output = capsys.readouterr().out

    assert "Shared fryer" in output
    assert "Shared utensils" in output
    assert output.count("[ENVIRONMENTAL RISK]") == 2


def test_print_cross_contact_risks_missing_key(capsys):
    io.print_cross_contact_risks({})

    assert "Cross-Contamination Risks: None" in (
        capsys.readouterr().out
    )

# --------------------------------------------------
# has_triggered_descendant()
# --------------------------------------------------

def test_has_triggered_descendant_direct_conflict():
    node = {
        "name": "Peanut sauce",
        "status": "Trigger",
        "conflict": "Peanut allergy",
        "children": [],
    }

    assert io.has_triggered_descendant(node) is True


def test_has_triggered_descendant_nested_conflict():
    node = {
        "name": "Dish",
        "children": [
            {
                "name": "Sauce",
                "status": "Safe",
                "conflict": None,
                "children": [
                    {
                        "name": "Peanut",
                        "status": "Trigger",
                        "conflict": "Peanut allergy",
                        "children": [],
                    }
                ],
            }
        ],
    }

    assert io.has_triggered_descendant(node) is True


def test_has_triggered_descendant_no_conflict():
    node = {
        "name": "Dish",
        "status": "Safe",
        "conflict": None,
        "children": [
            {
                "name": "Rice",
                "status": "Safe",
                "conflict": None,
                "children": [],
            }
        ],
    }

    assert io.has_triggered_descendant(node) is False


def test_has_triggered_descendant_trigger_without_conflict():
    node = {
        "name": "Dish",
        "status": "Trigger",
        "conflict": None,
        "children": [],
    }

    # A Trigger status alone is not enough for this function.
    assert io.has_triggered_descendant(node) is False

# --------------------------------------------------
# print_children_tree()
# --------------------------------------------------

def test_print_children_tree_single_child(capsys):
    tree = {
        "name": "Dish",
        "children": [
            {
                "name": "Rice",
                "status": "Safe",
                "conflict": None,
                "children": [],
            }
        ],
    }

    io.print_children_tree(tree)

    output = capsys.readouterr().out

    assert "└── Rice" in output
    assert "(Safe)" in output
    assert io.COLOR_GREEN in output


def test_print_children_tree_trigger_conflict_is_red(capsys):
    tree = {
        "name": "Dish",
        "children": [
            {
                "name": "Peanut sauce",
                "status": "Trigger",
                "conflict": "Peanut allergy",
                "children": [],
            }
        ],
    }

    io.print_children_tree(tree)

    output = capsys.readouterr().out

    assert "Peanut sauce" in output
    assert "[Trigger: Peanut allergy]" in output
    assert io.COLOR_RED in output


def test_print_children_tree_nested_child(capsys):
    tree = {
        "name": "Dish",
        "children": [
            {
                "name": "Sauce",
                "status": "Safe",
                "conflict": None,
                "children": [
                    {
                        "name": "Peanut",
                        "status": "Trigger",
                        "conflict": "Peanut allergy",
                        "children": [],
                    }
                ],
            }
        ],
    }

    io.print_children_tree(tree)

    output = capsys.readouterr().out

    assert "Sauce" in output
    assert "Peanut" in output
    assert "[Trigger: Peanut allergy]" in output


def test_print_children_tree_stall_insight(capsys):
    tree = {
        "name": "Dish",
        "children": [
            {
                "name": "Chicken",
                "status": "Safe",
                "conflict": None,
                "children": [],
                "stall_insight": "Cooked separately on request.",
            }
        ],
    }

    io.print_children_tree(tree)

    output = capsys.readouterr().out

    assert "Stall: Cooked separately on request." in output
    assert io.COLOR_YELLOW in output


def test_print_children_tree_empty_children(capsys):
    io.print_children_tree({"name": "Dish", "children": []})

    assert capsys.readouterr().out == ""


# --------------------------------------------------
# print_ingredient_breakdown_tree()
# --------------------------------------------------

def test_print_ingredient_breakdown_tree_none():
    # Empty result data should return without printing.
    assert io.print_ingredient_breakdown_tree(None) is None


def test_print_ingredient_breakdown_tree_valid(capsys):
    io.print_ingredient_breakdown_tree({
        "ingredient_tree": {
            "name": "Chicken Rice",
            "children": [
                {
                    "name": "Chicken",
                    "status": "Safe",
                    "conflict": None,
                    "children": [],
                }
            ],
        }
    })

    output = capsys.readouterr().out

    assert "FULL INGREDIENT BREAKDOWN" in output
    assert "Dish: Chicken Rice" in output
    assert "Chicken" in output

# --------------------------------------------------
# display_audit_result()
# --------------------------------------------------

def test_display_audit_result_contains_main_sections(capsys):
    io.display_audit_result(
        "test_user",
        "Test Stall",
        "Chicken Rice",
        {
            "allergies": ["egg"],
            "dietary_restrictions": ["vegetarian"],
            "others": ["g6pd"],
        },
        make_result(),
    )

    output = capsys.readouterr().out

    assert "DISH SAFETY AUDIT" in output
    assert "[USERNAME] test_user" in output
    assert "[DISH] Chicken Rice" in output
    assert "[LOCATION/STALL] Test Stall" in output
    assert "STALL STATUS: Known" in output
    assert "SAFE TO EAT" in output
    assert "FULL INGREDIENT BREAKDOWN" in output
    assert "ADVISORY DISCLAIMER" in output
    assert "Always verify with store owners" in output


@pytest.mark.parametrize(
    "knowledge, expected_emoji",
    [
        ("Known", "🟢"),
        ("Inferred", "🟡"),
        ("Unknown", "🔴"),
    ],
)
def test_display_audit_result_stall_status(
    knowledge, expected_emoji, capsys
):
    io.display_audit_result(
        "user",
        "stall",
        "dish",
        {},
        make_result(stall_knowledge=knowledge),
    )

    assert expected_emoji in capsys.readouterr().out


def test_display_audit_result_displays_conflicts(capsys):
    io.display_audit_result(
        "user",
        "stall",
        "dish",
        {},
        make_result(
            is_safe=False,
            risk_level="High",
            risk_score=95,
            allergy_conflicts=["Peanut"],
            cross_contact_risks=["Shared fryer"],
        ),
    )

    output = capsys.readouterr().out

    assert "NOT SAFE / AVOID" in output
    assert "Peanut" in output
    assert "Shared fryer" in output
    
# --------------------------------------------------
# get_user_inputs()
# --------------------------------------------------

def test_get_user_inputs_strips_whitespace(monkeypatch):
    answers = iter([
        "  Maxwell Food Centre  ",
        "  Chicken Rice  ",
    ])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    stall, dish = io.get_user_inputs()

    assert stall == "Maxwell Food Centre"
    assert dish == "Chicken Rice"


def test_get_user_inputs_allows_empty_strings(monkeypatch):
    answers = iter(["", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    stall, dish = io.get_user_inputs()

    # Documents current behavior: empty values are not rejected.
    assert stall == ""
    assert dish == ""

