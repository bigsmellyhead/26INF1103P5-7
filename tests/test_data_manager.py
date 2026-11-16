
import pytest
from unittest.mock import Mock

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import data_manager as dm
from database.database import Base
from database.models import User, AuditLog
from UserProfile import UserProfile


# ==================================================
# FIXTURE
# ==================================================

@pytest.fixture
def data_manager(monkeypatch):
    """
    Create a DataManager connected to a temporary SQLite database.

    This prevents tests from modifying the actual MySQL database.
    """

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    # Replace the real database session with the temporary one
    monkeypatch.setattr(dm, "SessionLocal", TestSessionLocal)

    manager = dm.DataManager()

    yield manager

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def sample_profile():
    """Create a reusable sample user profile."""

    return UserProfile(
        username="Alex",
        allergies=["Chicken egg"],
        dietary_restrictions=["Vegetarian"],
        other=["G6PD"],
        severity={
            "Chicken egg": "HIGH",
            "G6PD": "MED"
        }
    )


@pytest.fixture
def sample_audit_record():
    """Create a reusable sample audit record."""

    return {
        "stall": "Test Chicken Rice Stall",
        "dish": "Chicken Rice",
        "is_safe": False,
        "risk_level": "High",
        "risk_score": 85,
        "reasoning": "Contains a possible allergen.",
        "allergy_conflicts": ["Chicken egg"],
        "hidden_ingredients": ["Egg"],
        "cross_contact_risks": ["Shared cooking equipment"],
        "ingredient_tree": {"Rice": ["Water"]},
        "dietary_status": {"Vegetarian": "Not suitable"},
        "flags": ["Allergen detected"],
        "stall_knowledge": "KNOWN",
        "stall_specific_insights": "Uses shared equipment."
    }


# ==================================================
# TestDataManagerInitialization
# ==================================================

class TestDataManagerInitialization:

    def test_data_manager_creates_serializer(self, data_manager):
        from profile_serializer import ProfileSerializer

        assert isinstance(data_manager._serializer, ProfileSerializer)

    def test_initialize_database_calls_init_db(
        self, data_manager, monkeypatch
    ):
        mock_init = Mock()

        monkeypatch.setattr(dm, "init_db", mock_init)

        data_manager.initialize_database()

        mock_init.assert_called_once()


# ==================================================
# TestDataManagerUserProfiles
# ==================================================

class TestDataManagerUserProfiles:

    def test_save_and_get_user_profile(
        self, data_manager, sample_profile
    ):
        data_manager.save_user_profile(sample_profile)

        result = data_manager.get_user_profile("Alex")

        assert isinstance(result, UserProfile)
        assert result.username == "Alex"
        assert result.items_in("allergies") == ["Chicken egg"]
        assert result.items_in("dietary_restrictions") == ["Vegetarian"]
        assert result.items_in("other") == ["G6PD"]

    def test_get_user_profile_is_case_insensitive(
        self, data_manager, sample_profile
    ):
        data_manager.save_user_profile(sample_profile)

        result = data_manager.get_user_profile("aLeX")

        assert result is not None
        assert result.username == "Alex"

    def test_get_user_profile_returns_none_for_unknown_user(
        self, data_manager
    ):
        result = data_manager.get_user_profile("unknown")

        assert result is None

    def test_get_user_profile_returns_none_for_blank_username(
        self, data_manager
    ):
        assert data_manager.get_user_profile("") is None
        assert data_manager.get_user_profile("   ") is None

    def test_save_user_profile_updates_existing_user(
        self, data_manager
    ):
        original = UserProfile(
            username="Alex",
            dietary_restrictions=["Vegetarian"]
        )

        updated = UserProfile(
            username="ALEX",
            dietary_restrictions=["Vegan"]
        )

        data_manager.save_user_profile(original)
        data_manager.save_user_profile(updated)

        result = data_manager.get_user_profile("alex")

        assert result.username == "Alex"
        assert result.items_in("dietary_restrictions") == ["Vegan"]

    def test_saving_profile_preserves_other_users(
        self, data_manager
    ):
        alex = UserProfile("Alex", dietary_restrictions=["Halal"])
        sam = UserProfile("Sam", dietary_restrictions=["Vegan"])

        data_manager.save_user_profile(alex)
        data_manager.save_user_profile(sam)

        alex_updated = UserProfile(
            "Alex",
            dietary_restrictions=["Kosher"]
        )

        data_manager.save_user_profile(alex_updated)

        assert data_manager.get_user_profile(
            "Alex"
        ).items_in("dietary_restrictions") == ["Kosher"]

        assert data_manager.get_user_profile(
            "Sam"
        ).items_in("dietary_restrictions") == ["Vegan"]

    def test_saved_profile_preserves_severity(
        self, data_manager, sample_profile
    ):
        data_manager.save_user_profile(sample_profile)

        result = data_manager.get_user_profile("Alex")

        assert result.severity_label("Chicken egg") == "HIGH"
        assert result.severity_label("G6PD") == "MED"


# ==================================================
# TestDataManagerProfileValidation
# ==================================================

class TestDataManagerProfileValidation:

    def test_save_user_profile_rejects_non_profile(
        self, data_manager
    ):
        with pytest.raises(ValueError):
            data_manager.save_user_profile({"username": "Alex"})

    def test_save_user_profile_rejects_empty_username(
        self, data_manager
    ):
        profile = UserProfile("   ")

        with pytest.raises(ValueError):
            data_manager.save_user_profile(profile)


# ==================================================
# TestDataManagerSearch
# ==================================================

class TestDataManagerSearch:

    def test_search_user_profiles_by_partial_name(
        self, data_manager
    ):
        data_manager.save_user_profile(UserProfile("Alex"))
        data_manager.save_user_profile(UserProfile("Alexander"))
        data_manager.save_user_profile(UserProfile("Sam"))

        results = data_manager.search_user_profiles("Alex")

        usernames = [profile.username for profile in results]

        assert usernames == ["Alex", "Alexander"]

    def test_search_user_profiles_is_case_insensitive(
        self, data_manager
    ):
        data_manager.save_user_profile(UserProfile("Alexander"))

        results = data_manager.search_user_profiles("alex")

        assert len(results) == 1
        assert results[0].username == "Alexander"

    def test_search_user_profiles_returns_empty_for_no_match(
        self, data_manager
    ):
        data_manager.save_user_profile(UserProfile("Alex"))

        assert data_manager.search_user_profiles("unknown") == []

    def test_search_user_profiles_returns_empty_for_blank_input(
        self, data_manager
    ):
        assert data_manager.search_user_profiles("") == []
        assert data_manager.search_user_profiles("   ") == []

    def test_search_dietary_restriction(
        self, data_manager
    ):
        data_manager.save_user_profile(
            UserProfile("Alex", dietary_restrictions=["Vegetarian"])
        )

        data_manager.save_user_profile(
            UserProfile("Sam", dietary_restrictions=["Vegan"])
        )

        results = data_manager.search_dietary_restriction("vegetarian")

        assert len(results) == 1
        assert results[0].username == "Alex"

    def test_search_dietary_restriction_is_case_insensitive(
        self, data_manager
    ):
        data_manager.save_user_profile(
            UserProfile("Alex", allergies=["Chicken egg"])
        )

        results = data_manager.search_dietary_restriction("CHICKEN EGG")

        assert len(results) == 1
        assert results[0].username == "Alex"

    def test_search_dietary_restriction_supports_partial_match(
        self, data_manager
    ):
        data_manager.save_user_profile(
            UserProfile("Alex", allergies=["Chicken egg"])
        )

        results = data_manager.search_dietary_restriction("egg")

        assert len(results) == 1
        assert results[0].username == "Alex"

    def test_search_dietary_restriction_returns_empty_for_no_match(
        self, data_manager
    ):
        data_manager.save_user_profile(
            UserProfile("Alex", dietary_restrictions=["Vegetarian"])
        )

        assert data_manager.search_dietary_restriction("Halal") == []

    def test_search_dietary_restriction_returns_empty_for_blank_input(
        self, data_manager
    ):
        assert data_manager.search_dietary_restriction("") == []
        assert data_manager.search_dietary_restriction("   ") == []


# ==================================================
# TestDataManagerAuditLogs
# ==================================================

class TestDataManagerAuditLogs:

    def test_append_audit_log_creates_record(
        self, data_manager, sample_profile, sample_audit_record
    ):
        data_manager.append_audit_log(
            sample_profile, sample_audit_record
        )

        with dm.SessionLocal() as session:
            audit = session.scalar(select(AuditLog))

            assert audit is not None
            assert audit.stall == "Test Chicken Rice Stall"
            assert audit.dish == "Chicken Rice"
            assert audit.is_safe is False
            assert audit.risk_level == "High"
            assert audit.risk_score == 85

    def test_append_audit_log_creates_user_if_missing(
        self, data_manager, sample_profile, sample_audit_record
    ):
        data_manager.append_audit_log(
            sample_profile, sample_audit_record
        )

        result = data_manager.get_user_profile("Alex")

        assert result is not None
        assert result.username == "Alex"

    def test_append_audit_log_preserves_restriction_snapshot(
        self, data_manager, sample_profile, sample_audit_record
    ):
        data_manager.append_audit_log(
            sample_profile, sample_audit_record
        )

        with dm.SessionLocal() as session:
            audit = session.scalar(select(AuditLog))

            assert audit.restrictions_snapshot == {
                "allergies": ["Chicken egg"],
                "dietary_restrictions": ["Vegetarian"],
                "other": ["G6PD"],
                "severity": {
                    "Chicken egg": "HIGH",
                    "G6PD": "MED"
                }
            }

    def test_append_audit_log_preserves_nested_data(
        self, data_manager, sample_profile, sample_audit_record
    ):
        data_manager.append_audit_log(
            sample_profile, sample_audit_record
        )

        with dm.SessionLocal() as session:
            audit = session.scalar(select(AuditLog))

            assert audit.allergy_conflicts == ["Chicken egg"]
            assert audit.hidden_ingredients == ["Egg"]
            assert audit.cross_contact_risks == [
                "Shared cooking equipment"
            ]
            assert audit.ingredient_tree == {"Rice": ["Water"]}
            assert audit.dietary_status == {
                "Vegetarian": "Not suitable"
            }
            assert audit.flags == ["Allergen detected"]

    def test_append_multiple_audit_logs(
        self, data_manager, sample_profile, sample_audit_record
    ):
        second_record = {
            **sample_audit_record,
            "dish": "Fried Rice"
        }

        data_manager.append_audit_log(
            sample_profile, sample_audit_record
        )

        data_manager.append_audit_log(
            sample_profile, second_record
        )

        with dm.SessionLocal() as session:
            audits = session.scalars(select(AuditLog)).all()

            assert len(audits) == 2

    def test_append_audit_log_rejects_non_profile(
        self, data_manager, sample_audit_record
    ):
        with pytest.raises(ValueError):
            data_manager.append_audit_log(
                {"username": "Alex"},
                sample_audit_record
            )

    def test_append_audit_log_rejects_non_dictionary_record(
        self, data_manager, sample_profile
    ):
        with pytest.raises(ValueError):
            data_manager.append_audit_log(
                sample_profile, "invalid record"
            )

    def test_append_audit_log_uses_empty_defaults(
        self, data_manager, sample_profile
    ):
        data_manager.append_audit_log(
            sample_profile,
            {"dish": "Plain Rice"}
        )

        with dm.SessionLocal() as session:
            audit = session.scalar(select(AuditLog))

            assert audit.allergy_conflicts == []
            assert audit.hidden_ingredients == []
            assert audit.cross_contact_risks == []
            assert audit.ingredient_tree == {}
            assert audit.dietary_status == {}
            assert audit.flags == []


# ==================================================
# TestDataManagerAuditFiltering
# ==================================================

class TestDataManagerAuditFiltering:

    def test_filter_audit_history_by_restriction(
        self, data_manager, sample_profile, sample_audit_record
    ):
        data_manager.append_audit_log(
            sample_profile, sample_audit_record
        )

        results = data_manager.filter_audit_history_by_restrictions(
            ["Chicken egg"]
        )

        assert len(results) == 1

        audit, user = results[0]

        assert audit.dish == "Chicken Rice"
        assert user.username == "Alex"

    def test_filter_audit_history_is_case_insensitive(
        self, data_manager, sample_profile, sample_audit_record
    ):
        data_manager.append_audit_log(
            sample_profile, sample_audit_record
        )

        results = data_manager.filter_audit_history_by_restrictions(
            ["CHICKEN EGG"]
        )

        assert len(results) == 1

    def test_filter_audit_history_matches_any_selected_restriction(
        self, data_manager, sample_profile, sample_audit_record
    ):
        data_manager.append_audit_log(
            sample_profile, sample_audit_record
        )

        results = data_manager.filter_audit_history_by_restrictions(
            ["Vegan", "G6PD"]
        )

        assert len(results) == 1

    def test_filter_audit_history_returns_empty_for_no_match(
        self, data_manager, sample_profile, sample_audit_record
    ):
        data_manager.append_audit_log(
            sample_profile, sample_audit_record
        )

        results = data_manager.filter_audit_history_by_restrictions(
            ["Vegan"]
        )

        assert results == []

    def test_filter_audit_history_returns_empty_when_no_records(
        self, data_manager
    ):
        results = data_manager.filter_audit_history_by_restrictions(
            ["Chicken egg"]
        )

        assert results == []
