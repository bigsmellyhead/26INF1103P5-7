
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


