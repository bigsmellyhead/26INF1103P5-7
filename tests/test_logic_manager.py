import copy
import pytest

import logic_manager as lm


# --------------------------------------------------
# Helper data
# --------------------------------------------------

def make_node(
    name="Dish",
    status="Safe",
    conflict=None,
    children=None,
    **extra,
):
    node = {
        "name": name,
        "status": status,
        "conflict": conflict,
    }

    if children is not None:
        node["children"] = children

    node.update(extra)
    return node


def make_data(**overrides):
    """Create a valid baseline record for logic processing."""
    data = {
        "risk_score": 5,
        "risk_level": "Low",
        "is_safe": True,
        "stall_knowledge": "Known",
        "dietary_status": {},
        "allergy_conflicts": [],
        "cross_contact_risks": [],
        "ingredient_tree": make_node(
            "Chicken Rice",
            children=[
                make_node("Chicken", children=[]),
                make_node("Rice", children=[]),
            ],
        ),
    }
    data.update(overrides)
    return data


# --------------------------------------------------
# flatten_restrictions()
# --------------------------------------------------

def test_flatten_plain_restrictions():
    assert lm.flatten_restrictions(
        ["egg", "milk", "none", "halal"]
    ) == ["egg", "milk", "halal"]


def test_flatten_empty_plain_restrictions():
    assert lm.flatten_restrictions([]) == []


def test_flatten_grouped_restrictions():
    restrictions = {
        "allergies": ["egg", "milk"],
        "dietary_restrictions": ["halal"],
        "others": ["g6pd"],
    }

    assert lm.flatten_restrictions(restrictions) == [
        "egg", "milk", "halal", "g6pd"
    ]


def test_flatten_empty_grouped_restrictions():
    assert lm.flatten_restrictions({
        "allergies": [],
        "dietary_restrictions": [],
        "others": [],
    }) == []

