
import pytest

from logic_manager import LogicManager
from Data import AIAuditData, ResultAuditData
from UserProfile import UserProfile
from ingredient_tree_processor import IngredientTreeProcessor
from severity_policy import SeverityPolicy
from severity_level import SeverityLevel


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def make_profile(
    allergies=None,
    dietary_restrictions=None,
    other=None,
    severity=None,
):
    return UserProfile(
        username="TestUser",
        allergies=allergies or [],
        dietary_restrictions=dietary_restrictions or [],
        other=other or [],
        severity=severity or {},
    )


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


def make_ai_output(**overrides):
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


def make_audit_data(
    profile=None,
    ai_output=None,
    stall="Test Chicken Rice Stall",
    dish="Chicken Rice",
):
    if profile is None:
        profile = make_profile()

    if ai_output is None:
        ai_output = make_ai_output()

    return AIAuditData(
        profile,
        stall,
        dish,
        ai_output,
    )


# ==========================================================
# FIXTURES
# ==========================================================

@pytest.fixture
def manager():
    return LogicManager()


@pytest.fixture
def low_severity_profile():
    return make_profile(
        allergies=["Peanut"],
        severity={"Peanut": "LOW"},
    )


@pytest.fixture
def medium_severity_profile():
    return make_profile(
        allergies=["Peanut"],
        severity={"Peanut": "MED"},
    )


@pytest.fixture
def high_severity_profile():
    return make_profile(
        allergies=["Peanut"],
        severity={"Peanut": "HIGH"},
    )


# ==========================================================
# TEST LOGIC MANAGER INITIALIZATION
# ==========================================================

class TestLogicManagerInitialization:

    def test_creates_ingredient_tree_processor(self, manager):
        assert isinstance(
            manager._tree_processor,
            IngredientTreeProcessor,
        )

    def test_creates_severity_policy(self, manager):
        assert isinstance(
            manager._severity_policy,
            SeverityPolicy,
        )

    def test_creates_certification_requirements(self, manager):
        assert manager._certification_requirements == [
            "halal",
            "kosher",
        ]

    def test_each_manager_has_its_own_helpers(self):
        manager_one = LogicManager()
        manager_two = LogicManager()

        assert manager_one._tree_processor is not manager_two._tree_processor
        assert manager_one._severity_policy is not manager_two._severity_policy


# ==========================================================
# TEST SCORE HELPERS
# ==========================================================

class TestLogicManagerScoreHelpers:

    def test_raise_score_increases_score(self, manager):
        data = {
            "risk_score": 10,
            "flags": [],
        }

        manager._raise_score(data, 30, "Test reason")

        assert data["risk_score"] == 30
        assert len(data["flags"]) == 1
        assert "Test reason" in data["flags"][0]

    def test_raise_score_does_not_lower_score(self, manager):
        data = {
            "risk_score": 50,
            "flags": [],
        }

        manager._raise_score(data, 30, "Test reason")

        assert data["risk_score"] == 50
        assert data["flags"] == []

    def test_raise_score_does_nothing_at_exact_minimum(self, manager):
        data = {
            "risk_score": 30,
            "flags": [],
        }

        manager._raise_score(data, 30, "Test reason")

        assert data["risk_score"] == 30
        assert data["flags"] == []

    def test_cap_score_lowers_score(self, manager):
        data = {
            "risk_score": 90,
            "flags": [],
        }

        manager._cap_score(data, 59, "Test reason")

        assert data["risk_score"] == 59
        assert len(data["flags"]) == 1
        assert "Test reason" in data["flags"][0]

    def test_cap_score_does_not_increase_score(self, manager):
        data = {
            "risk_score": 20,
            "flags": [],
        }

        manager._cap_score(data, 59, "Test reason")

        assert data["risk_score"] == 20
        assert data["flags"] == []

    def test_cap_score_does_nothing_at_exact_maximum(self, manager):
        data = {
            "risk_score": 59,
            "flags": [],
        }

        manager._cap_score(data, 59, "Test reason")

        assert data["risk_score"] == 59
        assert data["flags"] == []


# ==========================================================
# TEST RISK BAND CALCULATION
# ==========================================================

class TestLogicManagerRiskBands:

    @pytest.mark.parametrize(
        "score, expected_level, expected_safe",
        [
            (0, "Low", True),
            (1, "Low", True),
            (29, "Low", True),
            (30, "Medium", False),
            (59, "Medium", False),
            (60, "High", False),
            (100, "High", False),
        ],
    )
    def test_apply_risk_band(
        self,
        manager,
        score,
        expected_level,
        expected_safe,
    ):
        data = {
            "risk_score": score,
            "risk_level": "Low",
            "is_safe": True,
        }

        manager._apply_risk_band(data)

        assert data["risk_level"] == expected_level
        assert data["is_safe"] is expected_safe


# ==========================================================
# TEST CERTIFICATION RULES
# ==========================================================

class TestLogicManagerCertificationRules:

    @pytest.mark.parametrize(
        "requirement",
        ["Halal", "Kosher"],
    )
    def test_compliant_certification_becomes_uncertain(
        self,
        manager,
        requirement,
    ):
        profile = make_profile()

        data = {
            "dietary_status": {
                requirement: "COMPLIANT",
            },
            "flags": [],
        }

        manager._apply_certification_rules(data, profile)

        assert data["dietary_status"][requirement] == "UNCERTAIN"
        assert any(
            "cannot verify a certification" in flag
            for flag in data["flags"]
        )

    @pytest.mark.parametrize(
        "requirement",
        ["Halal", "Kosher"],
    )
    def test_missing_user_certification_is_added(
        self,
        manager,
        requirement,
    ):
        profile = make_profile(
            dietary_restrictions=[requirement],
        )

        data = {
            "dietary_status": {},
            "flags": [],
        }

        manager._apply_certification_rules(data, profile)

        assert data["dietary_status"][requirement] == "UNCERTAIN"
        assert any(
            "was not assessed by the AI" in flag
            for flag in data["flags"]
        )

    def test_existing_certification_is_not_added_twice(self, manager):
        profile = make_profile(
            dietary_restrictions=["Halal"],
        )

        data = {
            "dietary_status": {
                "Halal food": "UNCERTAIN",
            },
            "flags": [],
        }

        manager._apply_certification_rules(data, profile)

        assert "Halal" not in data["dietary_status"]
        assert "Halal food" in data["dietary_status"]

    def test_non_compliant_certification_is_not_changed(self, manager):
        profile = make_profile()

        data = {
            "dietary_status": {
                "Halal": "NON-COMPLIANT",
            },
            "flags": [],
        }

        manager._apply_certification_rules(data, profile)

        assert data["dietary_status"]["Halal"] == "NON-COMPLIANT"


# ==========================================================
# TEST ALLERGY CONFLICT SEVERITY
# ==========================================================

class TestLogicManagerSeverityRules:

    def test_unknown_restriction_defaults_to_high(self, manager):
        profile = make_profile(
            allergies=["Egg"],
            severity={"Egg": "LOW"},
        )

        flags = []

        severity = manager._conflict_severity(
            {"restriction": "Peanut"},
            profile,
            flags,
        )

        assert severity == SeverityLevel.HIGH
        assert any(
            "not in the profile" in flag
            for flag in flags
        )

    def test_missing_saved_severity_defaults_to_high(self, manager):
        profile = make_profile(
            allergies=["Peanut"],
        )

        flags = []

        severity = manager._conflict_severity(
            {"restriction": "Peanut"},
            profile,
            flags,
        )

        assert severity == SeverityLevel.HIGH
        assert any(
            "No severity saved" in flag
            for flag in flags
        )

    def test_saved_high_severity_is_used(self, manager, high_severity_profile):
        flags = []

        severity = manager._conflict_severity(
            {"restriction": "Peanut"},
            high_severity_profile,
            flags,
        )

        assert severity == SeverityLevel.HIGH

    def test_saved_medium_severity_is_used(
        self,
        manager,
        medium_severity_profile,
    ):
        flags = []

        severity = manager._conflict_severity(
            {"restriction": "Peanut"},
            medium_severity_profile,
            flags,
        )

        assert severity == SeverityLevel.MED

    def test_saved_low_severity_is_used(self, manager, low_severity_profile):
        flags = []

        severity = manager._conflict_severity(
            {"restriction": "Peanut"},
            low_severity_profile,
            flags,
        )

        assert severity == SeverityLevel.LOW

    def test_apply_severity_rules_adds_severity_to_conflict(
        self,
        manager,
        high_severity_profile,
    ):
        data = {
            "risk_score": 5,
            "flags": [],
            "allergy_conflicts": [
                {
                    "restriction": "Peanut",
                    "ingredient": "Peanut sauce",
                    "presence": "CONFIRMED",
                }
            ],
        }

        severities = manager._apply_severity_rules(
            data,
            high_severity_profile,
        )

        assert data["allergy_conflicts"][0]["severity"] == SeverityLevel.HIGH
        assert severities == [SeverityLevel.HIGH]
        assert data["risk_score"] >= 80

    def test_apply_severity_rules_normalises_presence(
        self,
        manager,
        high_severity_profile,
    ):
        data = {
            "risk_score": 0,
            "flags": [],
            "allergy_conflicts": [
                {
                    "restriction": "Peanut",
                    "ingredient": "Peanut sauce",
                    "presence": "confirmed",
                }
            ],
        }

        manager._apply_severity_rules(
            data,
            high_severity_profile,
        )

        assert data["allergy_conflicts"][0]["presence"] == "CONFIRMED"

    def test_possible_high_severity_has_score_floor(
        self,
        manager,
        high_severity_profile,
    ):
        data = {
            "risk_score": 0,
            "flags": [],
            "allergy_conflicts": [
                {
                    "restriction": "Peanut",
                    "ingredient": "Peanut sauce",
                    "presence": "POSSIBLE",
                }
            ],
        }

        manager._apply_severity_rules(
            data,
            high_severity_profile,
        )

        assert data["risk_score"] == 60


# ==========================================================
# TEST INPUT VALIDATION
# ==========================================================

class TestLogicManagerInputValidation:

    @pytest.mark.parametrize(
        "invalid_input",
        [
            None,
            {},
            [],
            "invalid",
            123,
        ],
    )
    def test_rejects_non_ai_audit_data(self, manager, invalid_input):
        with pytest.raises(TypeError):
            manager.validate_and_process_logic(invalid_input)


# ==========================================================
# TEST FULL LOGIC PROCESSING
# ==========================================================

class TestLogicManagerIntegration:

    def test_returns_result_audit_data(self, manager):
        audit_data = make_audit_data()

        result = manager.validate_and_process_logic(audit_data)

        assert isinstance(result, ResultAuditData)

    def test_result_contains_original_profile_and_details(self, manager):
        profile = make_profile(
            allergies=["Peanut"],
            severity={"Peanut": "HIGH"},
        )

        audit_data = make_audit_data(
            profile=profile,
            stall="Test Stall",
            dish="Test Dish",
        )

        result = manager.validate_and_process_logic(audit_data)

        assert result.user_profile is profile
        assert result.stall == "Test Stall"
        assert result.dish == "Test Dish"

    def test_empty_profile_and_no_risks_remain_low(self, manager):
        audit_data = make_audit_data(
            ai_output=make_ai_output(
                risk_score=5,
                risk_level="Low",
            ),
        )

        result = manager.validate_and_process_logic(audit_data)

        assert result.result["risk_score"] == 5
        assert result.result["risk_level"] == "Low"
        assert result.result["is_safe"] is True
        assert result.result["flags"] == []

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
        self,
        manager,
        score,
        expected_score,
        expected_level,
        expected_safe,
    ):
        audit_data = make_audit_data(
            ai_output=make_ai_output(risk_score=score),
        )

        result = manager.validate_and_process_logic(audit_data)

        assert result.result["risk_score"] == expected_score
        assert result.result["risk_level"] == expected_level
        assert result.result["is_safe"] is expected_safe

    def test_flags_are_reset_on_each_call(self, manager):
        ai_output = make_ai_output()
        ai_output["flags"] = ["Old flag"]

        audit_data = make_audit_data(ai_output=ai_output)

        result = manager.validate_and_process_logic(audit_data)

        assert result.result["flags"] == []

    def test_ai_high_risk_level_cannot_be_lowered(self, manager):
        audit_data = make_audit_data(
            ai_output=make_ai_output(
                risk_score=5,
                risk_level="High",
            ),
        )

        result = manager.validate_and_process_logic(audit_data)

        assert result.result["risk_score"] >= 60
        assert result.result["risk_level"] == "High"
        assert result.result["is_safe"] is False

    def test_ai_medium_risk_level_cannot_be_lowered(self, manager):
        audit_data = make_audit_data(
            ai_output=make_ai_output(
                risk_score=5,
                risk_level="Medium",
            ),
        )

        result = manager.validate_and_process_logic(audit_data)

        assert result.result["risk_score"] >= 30
        assert result.result["risk_level"] in ["Medium", "High"]
        assert result.result["is_safe"] is False

    def test_non_compliant_dietary_status_raises_score_to_high(self, manager):
        audit_data = make_audit_data(
            ai_output=make_ai_output(
                dietary_status={
                    "Vegetarian": "NON-COMPLIANT",
                },
            ),
        )

        result = manager.validate_and_process_logic(audit_data)

        assert result.result["risk_score"] >= 60
        assert result.result["risk_level"] == "High"
        assert result.result["is_safe"] is False

    def test_uncertain_dietary_status_raises_score_to_medium(self, manager):
        audit_data = make_audit_data(
            ai_output=make_ai_output(
                dietary_status={
                    "Vegetarian": "UNCERTAIN",
                },
            ),
        )

        result = manager.validate_and_process_logic(audit_data)

        assert result.result["risk_score"] >= 30
        assert result.result["is_safe"] is False

    def test_unverified_stall_with_cross_contact_raises_score(
        self,
        manager,
    ):
        profile = make_profile(
            allergies=["Egg"],
            severity={"Egg": "HIGH"},
        )

        audit_data = make_audit_data(
            profile=profile,
            ai_output=make_ai_output(
                risk_score=10,
                stall_knowledge="Unknown",
                cross_contact_risks=["Shared fryer"],
            ),
        )

        result = manager.validate_and_process_logic(audit_data)

        assert result.result["risk_score"] >= 30
        assert result.result["is_safe"] is False
        assert any(
            "unverified stall with cross-contact risks" in flag
            for flag in result.result["flags"]
        )

    def test_unverified_stall_without_restrictions_does_not_apply_rule(
        self,
        manager,
    ):
        audit_data = make_audit_data(
            profile=make_profile(),
            ai_output=make_ai_output(
                risk_score=10,
                stall_knowledge="Unknown",
                cross_contact_risks=["Shared fryer"],
            ),
        )

        result = manager.validate_and_process_logic(audit_data)

        assert result.result["risk_score"] == 10
        assert result.result["is_safe"] is True

    def test_cross_contact_rule_requires_ai_score_at_least_10(
        self,
        manager,
    ):
        profile = make_profile(
            allergies=["Egg"],
            severity={"Egg": "HIGH"},
        )

        audit_data = make_audit_data(
            profile=profile,
            ai_output=make_ai_output(
                risk_score=9,
                stall_knowledge="Unknown",
                cross_contact_risks=["Shared fryer"],
            ),
        )

        result = manager.validate_and_process_logic(audit_data)

        assert result.result["risk_score"] == 9
        assert result.result["is_safe"] is True

    def test_conflict_without_trigger_adds_warning(self, manager):
        profile = make_profile(
            allergies=["Peanut"],
            severity={"Peanut": "HIGH"},
        )

        audit_data = make_audit_data(
            profile=profile,
            ai_output=make_ai_output(
                allergy_conflicts=[
                    {
                        "restriction": "Peanut",
                        "ingredient": "Peanut sauce",
                        "presence": "CONFIRMED",
                    }
                ],
            ),
        )

        result = manager.validate_and_process_logic(audit_data)

        assert any(
            "no ingredient is marked Trigger" in flag
            for flag in result.result["flags"]
        )

    def test_trigger_without_matching_conflict_raises_score(self, manager):
        profile = make_profile(
            allergies=["Peanut"],
            severity={"Peanut": "HIGH"},
        )

        audit_data = make_audit_data(
            profile=profile,
            ai_output=make_ai_output(
                risk_score=0,
                ingredient_tree=make_node(
                    "Dish",
                    children=[
                        make_node(
                            "Peanut sauce",
                            status="Trigger",
                            conflict="Peanut allergy",
                            children=[],
                        )
                    ],
                ),
            ),
        )

        result = manager.validate_and_process_logic(audit_data)

        assert result.result["risk_score"] >= 60
        assert result.result["is_safe"] is False

    def test_triggered_child_propagates_to_parent(self, manager):
        audit_data = make_audit_data(
            ai_output=make_ai_output(
                ingredient_tree=make_node(
                    "Dish",
                    children=[
                        make_node(
                            "Peanut",
                            status="Trigger",
                            conflict="Peanut allergy",
                            children=[],
                        )
                    ],
                ),
            ),
        )

        result = manager.validate_and_process_logic(audit_data)

        assert result.result["ingredient_tree"]["status"] == "Trigger"

    def test_repeated_child_is_removed_during_processing(self, manager):
        audit_data = make_audit_data(
            ai_output=make_ai_output(
                ingredient_tree=make_node(
                    "Rice",
                    children=[
                        make_node("Rice", children=[]),
                        make_node("Chicken", children=[]),
                    ],
                ),
            ),
        )

        result = manager.validate_and_process_logic(audit_data)

        child_names = [
            child["name"]
            for child in result.result["ingredient_tree"]["children"]
        ]

        assert child_names == ["Chicken"]

    def test_stall_insight_adds_flag(self, manager):
        audit_data = make_audit_data(
            ai_output=make_ai_output(
                ingredient_tree=make_node(
                    "Dish",
                    children=[
                        make_node(
                            "Peanut sauce",
                            status="Trigger",
                            conflict="Peanut allergy",
                            children=[],
                            stall_insight="Prepared using shared equipment",
                        )
                    ],
                ),
            ),
        )

        result = manager.validate_and_process_logic(audit_data)

        assert any(
            "Stall practice affects 'Peanut sauce'" in flag
            for flag in result.result["flags"]
        )


# ==========================================================
# TEST LOW-SEVERITY EXCEPTION
# ==========================================================

class TestLogicManagerLowSeverityException:

    def test_low_severity_confirmed_conflict_is_capped_at_59(
        self,
        manager,
        low_severity_profile,
    ):
        audit_data = make_audit_data(
            profile=low_severity_profile,
            ai_output=make_ai_output(
                risk_score=90,
                allergy_conflicts=[
                    {
                        "restriction": "Peanut",
                        "ingredient": "Peanut sauce",
                        "presence": "CONFIRMED",
                    }
                ],
            ),
        )

        result = manager.validate_and_process_logic(audit_data)

        assert result.result["risk_score"] == SeverityPolicy.MILD_ONLY_CAP
        assert result.result["risk_level"] == "Medium"
        assert result.result["is_safe"] is False

    def test_low_severity_possible_conflict_can_remain_low(
        self,
        manager,
        low_severity_profile,
    ):
        audit_data = make_audit_data(
            profile=low_severity_profile,
            ai_output=make_ai_output(
                risk_score=5,
                allergy_conflicts=[
                    {
                        "restriction": "Peanut",
                        "ingredient": "Peanut sauce",
                        "presence": "POSSIBLE",
                    }
                ],
            ),
        )

        result = manager.validate_and_process_logic(audit_data)

        assert result.result["risk_score"] == 10
        assert result.result["risk_level"] == "Low"
        assert result.result["is_safe"] is True

    def test_high_severity_conflict_is_not_capped(
        self,
        manager,
        high_severity_profile,
    ):
        audit_data = make_audit_data(
            profile=high_severity_profile,
            ai_output=make_ai_output(
                risk_score=90,
                allergy_conflicts=[
                    {
                        "restriction": "Peanut",
                        "ingredient": "Peanut sauce",
                        "presence": "CONFIRMED",
                    }
                ],
            ),
        )

        result = manager.validate_and_process_logic(audit_data)

        assert result.result["risk_score"] >= 60
        assert result.result["risk_level"] == "High"
        assert result.result["is_safe"] is False

    def test_low_severity_conflict_with_dietary_breach_is_not_capped(
        self,
        manager,
        low_severity_profile,
    ):
        audit_data = make_audit_data(
            profile=low_severity_profile,
            ai_output=make_ai_output(
                risk_score=90,
                allergy_conflicts=[
                    {
                        "restriction": "Peanut",
                        "ingredient": "Peanut sauce",
                        "presence": "CONFIRMED",
                    }
                ],
                dietary_status={
                    "Vegetarian": "NON-COMPLIANT",
                },
            ),
        )

        result = manager.validate_and_process_logic(audit_data)

        assert result.result["risk_score"] >= 60
        assert result.result["risk_level"] == "High"
        assert result.result["is_safe"] is False


# ==========================================================
# TEST COMBINED CONDITIONS
# ==========================================================

class TestLogicManagerCombinedConditions:

    def test_multiple_risks_use_highest_required_score(self, manager):
        profile = make_profile(
            allergies=["Peanut"],
            dietary_restrictions=["Vegetarian"],
            severity={"Peanut": "HIGH"},
        )

        audit_data = make_audit_data(
            profile=profile,
            ai_output=make_ai_output(
                risk_score=5,
                allergy_conflicts=[
                    {
                        "restriction": "Peanut",
                        "ingredient": "Peanut sauce",
                        "presence": "CONFIRMED",
                    }
                ],
                dietary_status={
                    "Vegetarian": "UNCERTAIN",
                },
            ),
        )

        result = manager.validate_and_process_logic(audit_data)

        assert result.result["risk_score"] >= 80
        assert result.result["risk_level"] == "High"
        assert result.result["is_safe"] is False
