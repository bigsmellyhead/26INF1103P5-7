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

# --------------------------------------------------
# remove_repeated_children()
# --------------------------------------------------

def test_remove_repeated_child_case_insensitive():
    tree = make_node(
        "Rice",
        children=[
            make_node("rice", children=[]),
            make_node("Chicken", children=[]),
        ],
    )

    lm.remove_repeated_children(tree)

    assert [child["name"] for child in tree["children"]] == [
        "Chicken"
    ]


def test_remove_repeated_trigger_child_propagates_conflict():
    tree = make_node(
        "Rice",
        status="Safe",
        conflict=None,
        children=[
            make_node(
                "Rice",
                status="Trigger",
                conflict="Rice allergy",
                children=[],
            )
        ],
    )

    lm.remove_repeated_children(tree)

    assert tree["status"] == "Trigger"
    assert tree["conflict"] == "Rice allergy"
    assert tree["children"] == []


def test_remove_repeated_child_keeps_existing_parent_conflict():
    tree = make_node(
        "Rice",
        status="Safe",
        conflict="Existing reason",
        children=[
            make_node(
                "Rice",
                status="Trigger",
                conflict="New reason",
                children=[],
            )
        ],
    )

    lm.remove_repeated_children(tree)

    assert tree["conflict"] == "Existing reason"


def test_remove_repeated_child_keeps_grandchildren():
    tree = make_node(
        "Rice",
        children=[
            make_node(
                "Rice",
                children=[
                    make_node("Peanut", children=[])
                ],
            )
        ],
    )

    lm.remove_repeated_children(tree)

    assert len(tree["children"]) == 1
    assert tree["children"][0]["name"] == "Peanut"


def test_remove_repeated_children_does_not_remove_different_names():
    tree = make_node(
        "Rice",
        children=[
            make_node("Brown Rice", children=[]),
            make_node("Rice Flour", children=[]),
        ],
    )

    lm.remove_repeated_children(tree)

    assert len(tree["children"]) == 2


def test_remove_repeated_children_handles_missing_children():
    tree = make_node("Rice")

    # Leaf nodes without a children key should be allowed.
    assert lm.remove_repeated_children(tree) is None
    assert "children" not in tree


# --------------------------------------------------
# collect_triggers()
# --------------------------------------------------

def test_collect_triggers_finds_trigger_leaf():
    leaf = make_node(
        "Peanut",
        status="Trigger",
        conflict="Peanut allergy",
    )
    found = []

    result = lm.collect_triggers(leaf, found, [])

    assert result == [leaf]


def test_collect_triggers_adds_missing_reason():
    leaf = make_node(
        "Unknown ingredient",
        status="Trigger",
        conflict=None,
    )
    flags = []

    found = lm.collect_triggers(leaf, [], flags)

    assert leaf in found
    assert leaf["conflict"] == "Flagged by the AI (no detail given)"
    assert any(
        "marked Trigger without a reason" in flag
        for flag in flags
    )


def test_collect_triggers_propagates_trigger_to_parent():
    parent = make_node(
        "Sauce",
        status="Safe",
        children=[
            make_node(
                "Peanut",
                status="Trigger",
                conflict="Peanut allergy",
            )
        ],
    )

    found = lm.collect_triggers(parent, [], [])

    assert parent["status"] == "Trigger"
    assert any(node["name"] == "Peanut" for node in found)
    assert any(node["name"] == "Sauce" for node in found)


def test_collect_triggers_does_not_replace_parent_conflict():
    parent = make_node(
        "Sauce",
        status="Safe",
        conflict="Existing conflict",
        children=[
            make_node(
                "Peanut",
                status="Trigger",
                conflict="Peanut allergy",
            )
        ],
    )

    lm.collect_triggers(parent, [], [])

    assert parent["status"] == "Trigger"
    assert parent["conflict"] == "Existing conflict"


def test_collect_triggers_does_not_duplicate_missing_reason_flag():
    leaf = make_node("Peanut", status="Trigger", conflict=None)
    flags = []

    lm.collect_triggers(leaf, [], flags)
    lm.collect_triggers(leaf, [], flags)

    assert len(flags) == 1
    assert flags == ["'Peanut' was marked Trigger without a reason."]

# --------------------------------------------------
# raise_score()
# --------------------------------------------------

def test_raise_score_raises_low_score():
    data = {"risk_score": 10, "flags": []}

    lm.raise_score(data, 30, "test reason")

    assert data["risk_score"] == 30
    assert len(data["flags"]) == 1
    assert "test reason" in data["flags"][0]


def test_raise_score_does_not_lower_score():
    data = {"risk_score": 50, "flags": []}

    lm.raise_score(data, 30, "test reason")

    assert data["risk_score"] == 50
    assert data["flags"] == []


def test_raise_score_at_exact_minimum():
    data = {"risk_score": 30, "flags": []}

    lm.raise_score(data, 30, "test reason")

    assert data["risk_score"] == 30
    assert data["flags"] == []

# --------------------------------------------------
# validate_and_process_logic(): score boundaries
# --------------------------------------------------

@pytest.mark.parametrize(
    "score, expected_score, expected_level, expected_safe",
    [
        (-20, 0, "Low", True),
        (0, 0, "Low", True),
        (29, 29, "Low", True),
        (30, 30, "Medium", False),
        (59, 59, "Medium", False),
        (60, 60, "High", False),
        (100, 100, "High", False),
        (150, 100, "High", False),
    ],
)
def test_score_boundaries(
    score, expected_score, expected_level, expected_safe
):
    data = make_data(risk_score=score)

    result = lm.validate_and_process_logic(data, [])

    assert result["risk_score"] == expected_score
    assert result["risk_level"] == expected_level
    assert result["is_safe"] is expected_safe


def test_flags_are_reset_on_each_call():
    data = make_data(flags=["Old flag"])

    result = lm.validate_and_process_logic(data, [])

    assert result["flags"] == []


# --------------------------------------------------
# validate_and_process_logic(): risk rules
# --------------------------------------------------

def test_allergy_conflict_raises_score_to_high():
    data = make_data(
        risk_score=10,
        allergy_conflicts=["Peanut"],
    )

    result = lm.validate_and_process_logic(data, ["peanut"])

    assert result["risk_score"] >= 60
    assert result["risk_level"] == "High"
    assert result["is_safe"] is False
    assert any(
        "conflict or non-compliant status" in flag
        for flag in result["flags"]
    )


def test_non_compliant_status_raises_score_to_high():
    data = make_data(
        risk_score=5,
        dietary_status={"Vegetarian": "NON-COMPLIANT"},
    )

    result = lm.validate_and_process_logic(data, ["vegetarian"])

    assert result["risk_score"] >= 60
    assert result["risk_level"] == "High"
    assert result["is_safe"] is False


def test_uncertain_status_raises_score_to_medium():
    data = make_data(
        risk_score=5,
        dietary_status={"Vegetarian": "UNCERTAIN"},
    )

    result = lm.validate_and_process_logic(data, ["vegetarian"])

    assert result["risk_score"] >= 30
    assert result["risk_level"] in ["Medium", "High"]
    assert result["is_safe"] is False


def test_trigger_ingredient_raises_score_to_medium():
    data = make_data(
        risk_score=5,
        ingredient_tree=make_node(
            "Dish",
            children=[
                make_node(
                    "Peanut",
                    status="Trigger",
                    conflict="Peanut allergy",
                )
            ],
        ),
    )

    result = lm.validate_and_process_logic(data, ["peanut"])

    assert result["risk_score"] >= 30
    assert result["is_safe"] is False
    assert any(
        "ingredient is marked Trigger" in flag
        for flag in result["flags"]
    )


def test_high_ai_risk_level_cannot_be_lowered():
    data = make_data(
        risk_score=5,
        risk_level="High",
    )

    result = lm.validate_and_process_logic(data, [])

    assert result["risk_score"] >= 60
    assert result["risk_level"] == "High"
    assert result["is_safe"] is False


def test_medium_ai_risk_level_cannot_be_lowered():
    data = make_data(
        risk_score=5,
        risk_level="Medium",
    )

    result = lm.validate_and_process_logic(data, [])

    assert result["risk_score"] >= 30
    assert result["risk_level"] in ["Medium", "High"]
    assert result["is_safe"] is False


def test_unverified_stall_with_cross_contact_raises_score():
    data = make_data(
        risk_score=10,
        stall_knowledge="Unknown",
        cross_contact_risks=["Shared fryer"],
    )

    result = lm.validate_and_process_logic(data, ["egg"])

    assert result["risk_score"] >= 30
    assert result["is_safe"] is False
    assert any(
        "unverified stall with cross-contact risks" in flag
        for flag in result["flags"]
    )


def test_unverified_stall_without_user_restrictions_does_not_apply_rule():
    data = make_data(
        risk_score=10,
        stall_knowledge="Unknown",
        cross_contact_risks=["Shared fryer"],
    )

    result = lm.validate_and_process_logic(data, [])

    assert result["risk_score"] == 10
    assert result["is_safe"] is True


def test_cross_contact_rule_requires_ai_score_at_least_10():
    data = make_data(
        risk_score=9,
        stall_knowledge="Unknown",
        cross_contact_risks=["Shared fryer"],
    )

    result = lm.validate_and_process_logic(data, ["egg"])

    assert result["risk_score"] == 9
    assert result["is_safe"] is True

# --------------------------------------------------
# Certification rules
# --------------------------------------------------

@pytest.mark.parametrize("requirement", ["Halal", "Kosher"])
def test_compliant_certification_becomes_uncertain(requirement):
    data = make_data(
        dietary_status={requirement: "COMPLIANT"},
    )

    result = lm.validate_and_process_logic(data, [])

    assert result["dietary_status"][requirement] == "UNCERTAIN"
    assert result["risk_score"] >= 30
    assert any(
        "cannot verify a certification" in flag
        for flag in result["flags"]
    )


@pytest.mark.parametrize("requirement", ["halal", "kosher"])
def test_missing_user_certification_is_added_as_uncertain(requirement):
    data = make_data(dietary_status={})

    result = lm.validate_and_process_logic(data, [requirement])

    assert result["dietary_status"][requirement.title()] == "UNCERTAIN"
    assert result["risk_score"] >= 30
    assert any(
        "was not assessed by the AI" in flag
        for flag in result["flags"]
    )


def test_already_assessed_certification_is_not_added_twice():
    data = make_data(
        dietary_status={"Halal food": "UNCERTAIN"},
    )

    result = lm.validate_and_process_logic(data, ["halal"])

    assert "Halal" not in result["dietary_status"]
    assert "Halal food" in result["dietary_status"]


def test_non_compliant_certification_stays_non_compliant():
    data = make_data(
        dietary_status={"Halal": "NON-COMPLIANT"},
    )

    result = lm.validate_and_process_logic(data, [])

    assert result["dietary_status"]["Halal"] == "NON-COMPLIANT"
    assert result["risk_score"] >= 60
