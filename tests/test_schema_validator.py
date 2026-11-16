
from schema_validator import SchemaValidator


class TestSchemaValidator:

    def setup_method(self):
        self.validator = SchemaValidator()

    def test_valid_string(self):
        result = self.validator.check_schema(
            "Alex",
            {"type": "STRING"}
        )

        assert result == []

    def test_valid_integer(self):
        result = self.validator.check_schema(
            25,
            {"type": "INTEGER"}
        )

        assert result == []

    def test_valid_boolean(self):
        result = self.validator.check_schema(
            True,
            {"type": "BOOLEAN"}
        )

        assert result == []

    def test_valid_array(self):
        result = self.validator.check_schema(
            ["Peanut", "Milk"],
            {
                "type": "ARRAY",
                "items": {"type": "STRING"}
            }
        )

        assert result == []

    def test_valid_object(self):
        result = self.validator.check_schema(
            {"name": "Alex"},
            {
                "type": "OBJECT",
                "required": ["name"],
                "properties": {
                    "name": {"type": "STRING"}
                }
            }
        )

        assert result == []

    def test_invalid_string_type(self):
        result = self.validator.check_schema(
            123,
            {"type": "STRING"}
        )

        assert result != []
        assert "wrong type" in result[0]

    def test_invalid_integer_type(self):
        result = self.validator.check_schema(
            "123",
            {"type": "INTEGER"}
        )

        assert result != []

    def test_invalid_boolean_type(self):
        result = self.validator.check_schema(
            "True",
            {"type": "BOOLEAN"}
        )

        assert result != []

    def test_null_value_not_allowed(self):
        result = self.validator.check_schema(
            None,
            {"type": "STRING"}
        )

        assert result != []
        assert "empty" in result[0]

    def test_null_value_allowed(self):
        result = self.validator.check_schema(
            None,
            {
                "type": "STRING",
                "nullable": True
            }
        )

        assert result == []

    def test_valid_enum_value(self):
        result = self.validator.check_schema(
            "Low",
            {
                "type": "STRING",
                "enum": ["Low", "Medium", "High"]
            }
        )

        assert result == []

    def test_invalid_enum_value(self):
        result = self.validator.check_schema(
            "Very High",
            {
                "type": "STRING",
                "enum": ["Low", "Medium", "High"]
            }
        )

        assert result != []
        assert "not allowed" in result[0]

    def test_value_below_minimum(self):
        result = self.validator.check_schema(
            5,
            {
                "type": "INTEGER",
                "minimum": 10
            }
        )

        assert result != []
        assert "too small" in result[0]

    def test_value_above_maximum(self):
        result = self.validator.check_schema(
            110,
            {
                "type": "INTEGER",
                "maximum": 100
            }
        )

        assert result != []
        assert "too big" in result[0]

    def test_value_within_minimum_and_maximum(self):
        result = self.validator.check_schema(
            50,
            {
                "type": "INTEGER",
                "minimum": 0,
                "maximum": 100
            }
        )

        assert result == []

    def test_array_exceeding_max_items(self):
        result = self.validator.check_schema(
            ["A", "B", "C"],
            {
                "type": "ARRAY",
                "maxItems": 2,
                "items": {"type": "STRING"}
            }
        )

        assert any("too many items" in problem for problem in result)

    def test_array_with_invalid_item(self):
        result = self.validator.check_schema(
            ["A", 123],
            {
                "type": "ARRAY",
                "items": {"type": "STRING"}
            }
        )

        assert result != []

    def test_missing_required_field(self):
        result = self.validator.check_schema(
            {"name": "Alex"},
            {
                "type": "OBJECT",
                "required": ["name", "age"],
                "properties": {
                    "name": {"type": "STRING"},
                    "age": {"type": "INTEGER"}
                }
            }
        )

        assert any("missing 'age'" in problem for problem in result)

    def test_invalid_nested_object(self):
        result = self.validator.check_schema(
            {
                "user": {
                    "age": "twenty"
                }
            },
            {
                "type": "OBJECT",
                "required": ["user"],
                "properties": {
                    "user": {
                        "type": "OBJECT",
                        "required": ["age"],
                        "properties": {
                            "age": {"type": "INTEGER"}
                        }
                    }
                }
            }
        )

        assert result != []

    def test_nested_object_with_valid_data(self):
        result = self.validator.check_schema(
            {
                "user": {
                    "age": 20
                }
            },
            {
                "type": "OBJECT",
                "required": ["user"],
                "properties": {
                    "user": {
                        "type": "OBJECT",
                        "required": ["age"],
                        "properties": {
                            "age": {"type": "INTEGER"}
                        }
                    }
                }
            }
        )

        assert result == []

    def test_error_message_includes_location(self):
        result = self.validator.check_schema(
            123,
            {"type": "STRING"},
            where="reply.name"
        )

        assert "reply.name" in result[0]
