
import pytest
from unittest.mock import Mock

from io_manager import IOManager
from models.UserProfile import UserProfile


# ==================================================
# TEST FIXTURE
# ==================================================

@pytest.fixture
def setup_io_manager():
    """Create an IOManager with a mocked DataManager."""
    data_manager = Mock()
    io_manager = IOManager(data_manager)

    return io_manager, data_manager


# ==================================================
# TestIOManagerAuthentication
# ==================================================

class TestIOManagerAuthentication:

    def test_is_admin_username(self):
        assert IOManager.is_admin_username("ADMIN") is True

    def test_normal_username_is_not_admin(self):
        assert IOManager.is_admin_username("test_user") is False

    def test_admin_username_is_case_sensitive(self):
        assert IOManager.is_admin_username("admin") is False

    def test_admin_login_success(self, setup_io_manager, monkeypatch):
        io_manager, _ = setup_io_manager

        monkeypatch.setattr(
            "io_manager.pwinput",
            lambda *args, **kwargs: "Admin123"
        )

        monkeypatch.setattr(
            io_manager,
            "_run_admin_menu",
            Mock()
        )

        io_manager.run_admin_login()

        io_manager._run_admin_menu.assert_called_once()

    def test_admin_login_wrong_password(
        self, setup_io_manager, monkeypatch, capsys
    ):
        io_manager, _ = setup_io_manager

        monkeypatch.setattr(
            "io_manager.pwinput",
            lambda *args, **kwargs: "wrong_password"
        )

        io_manager.run_admin_login()

        assert "Invalid admin password" in capsys.readouterr().out


# ==================================================
# TestIOManagerProfileDisplay
# ==================================================

class TestIOManagerProfileDisplay:

    def test_display_profile(self, setup_io_manager, capsys):
        io_manager, _ = setup_io_manager

        profile = UserProfile(
            username="test_user",
            allergies=["Egg"],
            dietary_restrictions=["Vegetarian"],
            other=["G6PD"],
            severity={
                "Egg": "HIGH",
                "G6PD": "MED"
            }
        )

        io_manager._display_profile(profile)

        output = capsys.readouterr().out

        assert "Username: test_user" in output
        assert "Allergies:" in output
        assert "Egg" in output
        assert "Dietary Restrictions:" in output
        assert "Vegetarian" in output
        assert "Other:" in output
        assert "G6PD" in output

    def test_display_empty_profile(self, setup_io_manager, capsys):
        io_manager, _ = setup_io_manager

        profile = UserProfile("new_user")

        io_manager._display_profile(profile)

        output = capsys.readouterr().out

        assert "Username: new_user" in output
        assert "Allergies: none" in output
        assert "Dietary Restrictions: none" in output
        assert "Other: none" in output


# ==================================================
# TestIOManagerProfileSearch
# ==================================================

class TestIOManagerProfileSearch:

    def test_search_user_profiles(
        self, setup_io_manager, monkeypatch, capsys
    ):
        io_manager, data_manager = setup_io_manager

        profile = UserProfile("test_user")

        monkeypatch.setattr(
            "builtins.input",
            lambda _: "test_user"
        )

        data_manager.search_user_profiles.return_value = [profile]

        io_manager._search_user_profiles()

        data_manager.search_user_profiles.assert_called_once_with(
            "test_user"
        )

        assert "Username: test_user" in capsys.readouterr().out

    def test_search_user_profiles_blank_input(
        self, setup_io_manager, monkeypatch, capsys
    ):
        io_manager, data_manager = setup_io_manager

        monkeypatch.setattr(
            "builtins.input",
            lambda _: "   "
        )

        io_manager._search_user_profiles()

        assert "Username cannot be blank." in capsys.readouterr().out

        data_manager.search_user_profiles.assert_not_called()

    def test_search_user_profiles_no_results(
        self, setup_io_manager, monkeypatch, capsys
    ):
        io_manager, data_manager = setup_io_manager

        monkeypatch.setattr(
            "builtins.input",
            lambda _: "unknown"
        )

        data_manager.search_user_profiles.return_value = []

        io_manager._search_user_profiles()

        assert "No matching user profiles found." in (
            capsys.readouterr().out
        )

    def test_search_dietary_restriction(
        self, setup_io_manager, monkeypatch, capsys
    ):
        io_manager, data_manager = setup_io_manager

        profile = UserProfile("test_user")

        monkeypatch.setattr(
            "builtins.input",
            lambda _: "egg"
        )

        data_manager.search_dietary_restriction.return_value = [profile]

        io_manager._search_dietary_restriction()

        data_manager.search_dietary_restriction.assert_called_once_with(
            "egg"
        )

        assert "Username: test_user" in capsys.readouterr().out

    def test_search_dietary_restriction_blank_input(
        self, setup_io_manager, monkeypatch, capsys
    ):
        io_manager, data_manager = setup_io_manager

        monkeypatch.setattr(
            "builtins.input",
            lambda _: " "
        )

        io_manager._search_dietary_restriction()

        assert "Restriction keyword cannot be blank." in (
            capsys.readouterr().out
        )

        data_manager.search_dietary_restriction.assert_not_called()


# ==================================================
# TestIOManagerRestrictionEditing
# ==================================================

class TestIOManagerRestrictionEditing:

    def test_edit_restrictions_updates_profile(
        self, setup_io_manager, monkeypatch
    ):
        io_manager, data_manager = setup_io_manager

        profile = UserProfile("test_user")

        monkeypatch.setattr(
            io_manager,
            "prompt_for_restrictions",
            lambda current=None: ["Chicken Egg", "Vegetarian", "G6PD"]
        )

        monkeypatch.setattr(
            io_manager,
            "prompt_for_severity",
            lambda names, current=None: {
                "Chicken Egg": "HIGH",
                "G6PD": "MED"
            }
        )

        monkeypatch.setattr(
            io_manager,
            "print_severity_summary",
            lambda restrictions: None
        )

        io_manager._edit_restrictions(profile)

        assert profile.username == "test_user"

        # The catalogue normalises restriction names to lowercase.
        assert profile.items_in("allergies") == ["chicken egg"]
        assert profile.items_in("dietary_restrictions") == ["vegetarian"]
        assert profile.items_in("other") == ["g6pd"]

        assert profile.severity_of("chicken egg") == "HIGH"
        assert profile.severity_of("g6pd") == "MED"

        # Confirm the existing profile object was updated, not replaced.
        assert isinstance(profile, UserProfile)


# ==================================================
# TestIOManagerAdminSearch
# ==================================================

class TestIOManagerAdminSearch:

    def test_filter_input_returns_selected_restrictions(
        self, setup_io_manager, monkeypatch
    ):
        io_manager, _ = setup_io_manager

        monkeypatch.setattr(
            io_manager,
            "prompt_for_restrictions",
            lambda: ["Egg", "Milk"]
        )

        result = io_manager._get_audit_filter_input()

        assert result == ["Egg", "Milk"]

    def test_filter_input_returns_none_when_empty(
        self, setup_io_manager, monkeypatch
    ):
        io_manager, _ = setup_io_manager

        monkeypatch.setattr(
            io_manager,
            "prompt_for_restrictions",
            lambda: ["none"]
        )

        assert io_manager._get_audit_filter_input() is None

    def test_display_filtered_history_empty(
        self, setup_io_manager, capsys
    ):
        io_manager, _ = setup_io_manager

        io_manager._display_filtered_audit_history(
            [],
            ["Egg"]
        )

        assert "No audit history found" in capsys.readouterr().out

    def test_display_filtered_history_with_records(
        self, setup_io_manager, capsys
    ):
        io_manager, _ = setup_io_manager

        audit = Mock()
        audit.created_at = "2026-11-16"
        audit.stall = "Test Stall"
        audit.dish = "Chicken Rice"
        audit.is_safe = True
        audit.risk_level = "Low"

        user = Mock()
        user.username = "test_user"

        io_manager._display_filtered_audit_history(
            [(audit, user)],
            ["Egg"]
        )

        output = capsys.readouterr().out

        assert "2026-11-16" in output
        assert "test_user" in output
        assert "Test Stall" in output
        assert "Chicken Rice" in output
        assert "True" in output
        assert "Low" in output


# ==================================================
# TestIOManagerUserInputs
# ==================================================

class TestIOManagerUserInputs:

    def test_get_user_inputs_strips_whitespace(
        self, setup_io_manager, monkeypatch
    ):
        io_manager, _ = setup_io_manager

        answers = iter([
            "  Maxwell Food Centre  ",
            "  Chicken Rice  "
        ])

        monkeypatch.setattr(
            "builtins.input",
            lambda _: next(answers)
        )

        stall, dish = io_manager.get_user_inputs()

        assert stall == "Maxwell Food Centre"
        assert dish == "Chicken Rice"

    def test_get_user_inputs_allows_empty_strings(
        self, setup_io_manager, monkeypatch
    ):
        io_manager, _ = setup_io_manager

        answers = iter(["", ""])

        monkeypatch.setattr(
            "builtins.input",
            lambda _: next(answers)
        )

        stall, dish = io_manager.get_user_inputs()

        assert stall == ""
        assert dish == ""


# ==================================================
# TestIOManagerAuditDisplay
# ==================================================

class TestIOManagerAuditDisplay:

    def test_display_audit_result_delegates_to_renderer(
        self, setup_io_manager
    ):
        io_manager, _ = setup_io_manager

        # Replace the renderer with a mock.
        renderer = Mock()
        io_manager._IOManager__audit_renderer = renderer

        result = Mock()

        io_manager.display_audit_result(result)

        renderer.render_sections.assert_called_once_with(result)


# ==================================================
# TestIOManagerErrorDisplay
# ==================================================

class TestIOManagerErrorDisplay:

    def test_display_error(self, setup_io_manager, capsys):
        io_manager, _ = setup_io_manager

        io_manager.display_error("Temporary AI error")

        assert "Temporary AI error" in capsys.readouterr().out
