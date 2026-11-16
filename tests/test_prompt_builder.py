
from prompt_builder import PromptBuilder


class FakeProfile:
    def __init__(self, restrictions=None, severities=None):
        self.restrictions = restrictions or {
            "allergies": [],
            "dietary_restrictions": [],
            "other": []
        }

        self.severities = severities or {}

    def items_in(self, category):
        return self.restrictions.get(category, [])

    def severity_label(self, name):
        return self.severities.get(name)


class TestPromptBuilder:

    def setup_method(self):
        self.builder = PromptBuilder()

    def test_initialization(self):
        assert self.builder.ai_prompt is not None
        assert len(self.builder.ai_prompt) > 0

    def test_system_prompt_returns_prompt(self):
        result = self.builder.system_prompt()

        assert result == self.builder.ai_prompt
        assert len(result) > 0

    def test_system_prompt_contains_food_safety_instructions(self):
        result = self.builder.system_prompt()

        assert "food safety" in result
        assert "cross-contact" in result
        assert "risk_score" in result

    def test_sanitise_removes_angle_brackets(self):
        result = self.builder._sanitise(
            "<script>alert('hello')</script>"
        )

        assert result == "scriptalert('hello')/script"

    def test_format_group_with_severity(self):
        profile = FakeProfile(
            restrictions={
                "allergies": ["Peanut", "Milk"],
                "dietary_restrictions": [],
                "other": []
            },
            severities={
                "Peanut": "HIGH",
                "Milk": "MED"
            }
        )

        result = self.builder._format_group(
            profile,
            "allergies"
        )

        assert result == "Peanut (HIGH), Milk (MED)"

    def test_format_group_without_severity(self):
        profile = FakeProfile(
            restrictions={
                "allergies": [],
                "dietary_restrictions": ["Vegetarian"],
                "other": []
            }
        )

        result = self.builder._format_group(
            profile,
            "dietary_restrictions"
        )

        assert result == "Vegetarian"

    def test_format_empty_group_returns_none(self):
        profile = FakeProfile()

        result = self.builder._format_group(
            profile,
            "allergies"
        )

        assert result == "none"

    def test_restrictions_to_groups(self):
        profile = FakeProfile(
            restrictions={
                "allergies": ["Peanut"],
                "dietary_restrictions": ["Vegetarian"],
                "other": ["Lactose"]
            },
            severities={
                "Peanut": "HIGH",
                "Lactose": "MED"
            }
        )

        result = self.builder._restrictions_to_groups(profile)

        assert result == (
            "Peanut (HIGH)",
            "Vegetarian",
            "Lactose (MED)"
        )

    def test_build_user_message_contains_stall_and_dish(self):
        profile = FakeProfile()

        result = self.builder.build_user_message(
            "Stall A",
            "Chicken Rice",
            profile
        )

        assert "<stall>Stall A</stall>" in result
        assert "<dish>Chicken Rice</dish>" in result

    def test_build_user_message_contains_restrictions(self):
        profile = FakeProfile(
            restrictions={
                "allergies": ["Peanut"],
                "dietary_restrictions": ["Vegetarian"],
                "other": ["Lactose"]
            },
            severities={
                "Peanut": "HIGH",
                "Lactose": "MED"
            }
        )

        result = self.builder.build_user_message(
            "Stall A",
            "Chicken Rice",
            profile
        )

        assert "Peanut (HIGH)" in result
        assert "Vegetarian" in result
        assert "Lactose (MED)" in result

    def test_build_user_message_with_empty_profile(self):
        profile = FakeProfile()

        result = self.builder.build_user_message(
            "Stall A",
            "Chicken Rice",
            profile
        )

        assert "<allergies>none</allergies>" in result
        assert "<dietary>none</dietary>" in result
        assert "<other>none</other>" in result

    def test_build_user_message_sanitises_stall_and_dish(self):
        profile = FakeProfile()

        result = self.builder.build_user_message(
            "Stall <A>",
            "Chicken <Rice>",
            profile
        )

        assert "Stall A" in result
        assert "Chicken Rice" in result
        assert "<stall>Stall <A></stall>" not in result
        assert "<dish>Chicken <Rice></dish>" not in result

    def test_build_user_message_sanitises_restrictions(self):
        profile = FakeProfile(
            restrictions={
                "allergies": ["Peanut <script>"],
                "dietary_restrictions": [],
                "other": []
            },
            severities={
                "Peanut <script>": "HIGH"
            }
        )

        result = self.builder.build_user_message(
            "Stall A",
            "Chicken Rice",
            profile
        )

        assert "<script>" not in result
        assert "Peanut script (HIGH)" in result
