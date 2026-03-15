"""Tests for standalone JSON schema validator."""
import pytest
from pylemura.tools.schema_validator import validate_json_schema, ValidationError


def test_valid_object():
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
        "required": ["name"],
    }
    validate_json_schema({"name": "Alice", "age": 30}, schema)


def test_missing_required():
    schema = {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}
    with pytest.raises(ValidationError):
        validate_json_schema({}, schema)


def test_wrong_type():
    with pytest.raises(ValidationError):
        validate_json_schema("hello", {"type": "integer"})


def test_enum():
    schema = {"enum": ["a", "b", "c"]}
    validate_json_schema("a", schema)
    with pytest.raises(ValidationError):
        validate_json_schema("d", schema)


def test_string_min_max_length():
    schema = {"type": "string", "minLength": 2, "maxLength": 5}
    validate_json_schema("abc", schema)
    with pytest.raises(ValidationError):
        validate_json_schema("a", schema)
    with pytest.raises(ValidationError):
        validate_json_schema("toolong", schema)


def test_number_bounds():
    schema = {"type": "number", "minimum": 0, "maximum": 10}
    validate_json_schema(5, schema)
    with pytest.raises(ValidationError):
        validate_json_schema(-1, schema)


def test_array_items():
    schema = {"type": "array", "items": {"type": "integer"}}
    validate_json_schema([1, 2, 3], schema)
    with pytest.raises(ValidationError):
        validate_json_schema([1, "x"], schema)


def test_nested_object():
    schema = {
        "type": "object",
        "properties": {
            "address": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            }
        },
        "required": ["address"],
    }
    validate_json_schema({"address": {"city": "Paris"}}, schema)
    with pytest.raises(ValidationError):
        validate_json_schema({"address": {}}, schema)


def test_any_of():
    schema = {"anyOf": [{"type": "string"}, {"type": "integer"}]}
    validate_json_schema("hello", schema)
    validate_json_schema(42, schema)
    with pytest.raises(ValidationError):
        validate_json_schema([], schema)
