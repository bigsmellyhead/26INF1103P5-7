
import json
import logging
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest
import ai_manager as am


# =========================================================
# HELPERS
# =========================================================

def valid_reply():
    """Return a valid example response matching ai_output_schema."""
    return {
        "stall_knowledge": "Inferred",
        "is_safe": True,
        "risk_level": "Low",
        "risk_score": 10,
        "stall_specific_insights": "No notable difference.",
        "reasoning": "No listed restriction appears to conflict.",
        "hidden_ingredients": [],
        "cross_contact_risks": [],
        "dietary_status": [
            {"requirement": "Vegan", "status": "COMPLIANT"}
        ],
        "allergy_conflicts": [],
        "ingredient_tree": {
            "name": "Chicken Rice",
            "status": "Safe",
            "conflict": None,
            "stall_insight": None,
            "children": [
                {
                    "name": "Rice",
                    "status": "Safe",
                    "conflict": None,
                    "stall_insight": None,
                    "children": [
                        {
                            "name": "Rice grains",
                            "status": "Safe",
                            "conflict": None,
                            "stall_insight": None,
                        }
                    ],
                }
            ],
        },
    }


def response(text):
    return SimpleNamespace(text=text)


def mock_gemini(monkeypatch, results=None, side_effect=None):
    """Mock Gemini so tests never make real API requests."""
    client = Mock()

    if side_effect is not None:
        client.models.generate_content.side_effect = side_effect
    elif results is not None:
        client.models.generate_content.side_effect = results
    else:
        client.models.generate_content.return_value = response(
            json.dumps(valid_reply())
        )

    monkeypatch.setattr(
        am.genai, "Client", Mock(return_value=client)
    )
    monkeypatch.setattr(am, "display_api_key_error", Mock())
    monkeypatch.setattr(am, "display_attempt_error", Mock())

    return client


# =========================================================
# 1. restrictions_to_groups()
# =========================================================

def test_restrictions_all_groups():
    result = am.restrictions_to_groups({
        "allergies": ["Egg", "Milk"],
        "dietary_restrictions": ["Vegan", "Halal"],
        "other": ["G6PD"],
    })

    assert result == (
        "Egg, Milk", "Vegan, Halal", "G6PD"
    )


def test_restrictions_empty_lists():
    assert am.restrictions_to_groups({
        "allergies": [],
        "dietary_restrictions": [],
        "other": [],
    }) == ("none", "none", "none")


def test_restrictions_missing_keys():
    assert am.restrictions_to_groups({}) == (
        "none", "none", "none"
    )


def test_restrictions_partial_keys():
    assert am.restrictions_to_groups({
        "allergies": ["Peanuts"]
    }) == ("Peanuts", "none", "none")


def test_restrictions_preserve_order():
    assert am.restrictions_to_groups({
        "allergies": ["A", "B", "C"],
        "dietary_restrictions": ["X", "Y"],
        "other": ["Z"],
    }) == ("A, B, C", "X, Y", "Z")


def test_restrictions_do_not_modify_input():
    original = {"allergies": ["Egg"], "other": []}
    saved = {"allergies": ["Egg"], "other": []}

    am.restrictions_to_groups(original)

    assert original == saved


# =========================================================
# 2. check_schema(): BASIC TYPES AND NULL
# =========================================================

@pytest.mark.parametrize("schema_type,value,schema", [
    ("STRING", "hello", {"type": "STRING"}),
    ("INTEGER", 123, {"type": "INTEGER"}),
    ("BOOLEAN", True, {"type": "BOOLEAN"}),
    ("ARRAY", [], {
        "type": "ARRAY",
        "items": {"type": "STRING"}
    }),
    ("OBJECT", {}, {
        "type": "OBJECT",
        "required": [],
        "properties": {}
    }),
])
def test_valid_basic_types(schema_type, value, schema):
    assert am.check_schema(value, schema) == []


@pytest.mark.parametrize("schema_type,value", [
    ("STRING", 123),
    ("INTEGER", "123"),
    ("BOOLEAN", 1),
    ("ARRAY", {}),
    ("OBJECT", []),
])
def test_invalid_basic_types(schema_type, value):
    problems = am.check_schema(
        value, {"type": schema_type}
    )

    assert any("wrong type" in p for p in problems)


def test_null_not_allowed():
    assert am.check_schema(
        None, {"type": "STRING"}
    ) == ["reply is empty"]


def test_null_allowed():
    assert am.check_schema(
        None, {"type": "STRING", "nullable": True}
    ) == []


def test_nullable_does_not_allow_wrong_type():
    assert am.check_schema(
        123, {"type": "STRING", "nullable": True}
    )
# =========================================================
# 3. check_schema(): ENUMS AND NUMBER LIMITS
# =========================================================

@pytest.mark.parametrize("value", ["Safe", "Trigger"])
def test_valid_enum(value):
    assert am.check_schema(value, {
        "type": "STRING",
        "enum": ["Safe", "Trigger"],
    }) == []


def test_invalid_enum():
    problems = am.check_schema("Danger", {
        "type": "STRING",
        "enum": ["Safe", "Trigger"],
    })

    assert any("not allowed" in p for p in problems)


@pytest.mark.parametrize("value", [0, 50, 100])
def test_valid_number_boundaries(value):
    assert am.check_schema(value, {
        "type": "INTEGER",
        "minimum": 0,
        "maximum": 100,
    }) == []


def test_number_below_minimum():
    problems = am.check_schema(-1, {
        "type": "INTEGER", "minimum": 0
    })

    assert any("too small" in p for p in problems)


def test_number_above_maximum():
    problems = am.check_schema(101, {
        "type": "INTEGER", "maximum": 100
    })

    assert any("too big" in p for p in problems)


def test_enum_and_range_both_checked():
    problems = am.check_schema(5, {
        "type": "INTEGER",
        "enum": [1, 2, 3],
        "minimum": 1,
        "maximum": 3,
    })

    assert any("not allowed" in p for p in problems)
    assert any("too big" in p for p in problems)

# =========================================================
# 4. check_schema(): ARRAYS
# =========================================================

def test_valid_array():
    assert am.check_schema(["Egg", "Milk"], {
        "type": "ARRAY",
        "items": {"type": "STRING"},
    }) == []


def test_empty_array():
    assert am.check_schema([], {
        "type": "ARRAY",
        "items": {"type": "STRING"},
    }) == []


def test_invalid_array_item():
    problems = am.check_schema(["Egg", 123], {
        "type": "ARRAY",
        "items": {"type": "STRING"},
    })

    assert any("wrong type" in p for p in problems)


def test_array_exceeds_max_items():
    problems = am.check_schema(["A", "B", "C", "D"], {
        "type": "ARRAY",
        "items": {"type": "STRING"},
        "maxItems": 3,
    })

    assert any("too many items" in p for p in problems)


def test_array_at_max_items():
    assert am.check_schema(["A", "B", "C"], {
        "type": "ARRAY",
        "items": {"type": "STRING"},
        "maxItems": 3,
    }) == []


def test_nested_array_invalid_item():
    problems = am.check_schema([[1, 2], [3, "bad"]], {
        "type": "ARRAY",
        "items": {
            "type": "ARRAY",
            "items": {"type": "INTEGER"},
        },
    })

    assert problems

def test_array_schema_missing_items_raises_error():
    schema = {
        "type": "ARRAY",
        "maxItems": 5,
    }

    with pytest.raises(KeyError):
        am.check_schema([1, 2, 3], schema)

# =========================================================
# 5. check_schema(): OBJECTS
# =========================================================

def test_valid_object():
    schema = {
        "type": "OBJECT",
        "properties": {
            "name": {"type": "STRING"},
            "score": {"type": "INTEGER"},
        },
        "required": ["name", "score"],
    }

    assert am.check_schema(
        {"name": "Dish", "score": 50}, schema
    ) == []


def test_missing_required_key():
    problems = am.check_schema({
        "name": "Dish"
    }, {
        "type": "OBJECT",
        "properties": {
            "name": {"type": "STRING"},
            "score": {"type": "INTEGER"},
        },
        "required": ["name", "score"],
    })

    assert any("missing 'score'" in p for p in problems)


def test_multiple_missing_keys():
    problems = am.check_schema({}, {
        "type": "OBJECT",
        "properties": {
            "a": {"type": "STRING"},
            "b": {"type": "STRING"},
        },
        "required": ["a", "b"],
    })

    assert any("missing 'a'" in p for p in problems)
    assert any("missing 'b'" in p for p in problems)


def test_invalid_nested_property():
    problems = am.check_schema({"name": 123}, {
        "type": "OBJECT",
        "properties": {"name": {"type": "STRING"}},
        "required": ["name"],
    })

    assert any("wrong type" in p for p in problems)


def test_nested_object_invalid_enum():
    problems = am.check_schema({
        "items": [{"status": "Unknown"}]
    }, {
        "type": "OBJECT",
        "properties": {
            "items": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "status": {
                            "type": "STRING",
                            "enum": ["Safe", "Trigger"],
                        }
                    },
                    "required": ["status"],
                },
            }
        },
        "required": ["items"],
    })

    assert any("not allowed" in p for p in problems)


def test_unexpected_object_keys_currently_accepted():
    # Documents a limitation in the current validator.
    assert am.check_schema({
        "name": "Dish", "unexpected": True
    }, {
        "type": "OBJECT",
        "properties": {"name": {"type": "STRING"}},
        "required": ["name"],
    }) == []


def test_object_schema_missing_properties_raises_error():
    with pytest.raises(KeyError):
        am.check_schema({}, {
            "type": "OBJECT", "required": []
        })

# =========================================================
# 6. APPLICATION-SPECIFIC SCHEMAS
# =========================================================

def test_valid_leaf_node():
    assert am.check_schema({
        "name": "Peanuts",
        "status": "Trigger",
        "conflict": "Contains nuts",
        "stall_insight": None,
    }, am.leaf_node_schema) == []


def test_valid_safe_leaf_node():
    assert am.check_schema({
        "name": "Rice grains",
        "status": "Safe",
        "conflict": None,
        "stall_insight": None,
    }, am.leaf_node_schema) == []


def test_leaf_missing_key():
    problems = am.check_schema({
        "name": "Peanuts",
        "status": "Trigger",
        "conflict": "Contains nuts",
    }, am.leaf_node_schema)

    assert any("stall_insight" in p for p in problems)


def test_leaf_invalid_status():
    problems = am.check_schema({
        "name": "Peanuts",
        "status": "Danger",
        "conflict": "Contains nuts",
        "stall_insight": None,
    }, am.leaf_node_schema)

    assert any("not allowed" in p for p in problems)


def test_leaf_extra_children_currently_accepted():
    # Current validator ignores undeclared object properties.
    assert am.check_schema({
        "name": "Peanuts",
        "status": "Trigger",
        "conflict": "Contains nuts",
        "stall_insight": None,
        "children": [],
    }, am.leaf_node_schema) == []


def test_valid_component_node():
    assert am.check_schema({
        "name": "Sauce",
        "status": "Trigger",
        "conflict": None,
        "stall_insight": None,
        "children": [{
            "name": "Soy sauce",
            "status": "Trigger",
            "conflict": "Contains soy",
            "stall_insight": None,
        }],
    }, am.component_node_schema) == []


def test_valid_ingredient_tree():
    assert am.check_schema(
        valid_reply()["ingredient_tree"],
        am.ingredient_tree_schema,
    ) == []


def test_valid_complete_output():
    assert am.check_schema(
        valid_reply(), am.ai_output_schema
    ) == []


@pytest.mark.parametrize("field,bad_value", [
    ("stall_knowledge", "Maybe"),
    ("is_safe", "True"),
    ("risk_level", "Severe"),
    ("risk_score", -1),
    ("risk_score", 101),
    ("stall_specific_insights", None),
    ("reasoning", 123),
    ("hidden_ingredients", "Peanuts"),
    ("cross_contact_risks", ["A", "B", "C", "D"]),
    ("allergy_conflicts", "Peanuts"),
    ("ingredient_tree", []),
])
def test_invalid_top_level_fields(field, bad_value):
    data = valid_reply()
    data[field] = bad_value

    assert am.check_schema(data, am.ai_output_schema)


def test_invalid_dietary_status_enum():
    data = valid_reply()
    data["dietary_status"] = [{
        "requirement": "Vegan",
        "status": "MAYBE",
    }]

    assert am.check_schema(data, am.ai_output_schema)


def test_missing_top_level_key():
    data = valid_reply()
    del data["risk_score"]

    problems = am.check_schema(data, am.ai_output_schema)

    assert any("missing 'risk_score'" in p for p in problems)

