"""Standalone JSON Schema validator — zero dependencies.
Supports: type, properties, required, enum, minimum, maximum,
          minLength, maxLength, pattern, items, additionalProperties,
          anyOf, oneOf, allOf, $ref (local definitions only).
"""
from __future__ import annotations
import re
from typing import Any, Optional


class ValidationError(Exception):
    def __init__(self, path: str, message: str) -> None:
        super().__init__(f"[{path}] {message}")
        self.path = path


def validate_json_schema(
    value: Any,
    schema: dict[str, Any],
    path: str = "#",
    definitions: Optional[dict[str, Any]] = None,
) -> None:
    """Validate *value* against *schema*. Raises ValidationError on failure."""
    if definitions is None:
        definitions = schema.get("$defs") or schema.get("definitions") or {}

    if "$ref" in schema:
        ref = schema["$ref"]
        def_name = ref.split("/")[-1]
        ref_schema = definitions.get(def_name)
        if ref_schema is None:
            raise ValidationError(path, f"Unknown $ref: {ref}")
        validate_json_schema(value, ref_schema, path, definitions)
        return

    schema_type = schema.get("type")

    # --- anyOf / oneOf / allOf ---
    if "anyOf" in schema:
        errors = []
        for sub in schema["anyOf"]:
            try:
                validate_json_schema(value, sub, path, definitions)
                return
            except ValidationError as e:
                errors.append(str(e))
        raise ValidationError(path, "Value does not match any of anyOf schemas: " + "; ".join(errors))

    if "oneOf" in schema:
        matched = 0
        errors = []
        for sub in schema["oneOf"]:
            try:
                validate_json_schema(value, sub, path, definitions)
                matched += 1
            except ValidationError as e:
                errors.append(str(e))
        if matched != 1:
            raise ValidationError(path, f"Value must match exactly one of oneOf schemas (matched {matched})")

    if "allOf" in schema:
        for sub in schema["allOf"]:
            validate_json_schema(value, sub, path, definitions)

    # --- null ---
    if value is None:
        if schema_type and schema_type != "null":
            raise ValidationError(path, f"Expected {schema_type}, got null")
        return

    # --- enum ---
    if "enum" in schema:
        if value not in schema["enum"]:
            raise ValidationError(path, f"Value {value!r} not in enum {schema['enum']}")

    # --- const ---
    if "const" in schema:
        if value != schema["const"]:
            raise ValidationError(path, f"Value {value!r} != const {schema['const']!r}")

    # --- type check ---
    if schema_type:
        _check_type(value, schema_type, path)

    # --- string ---
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            raise ValidationError(path, f"String length {len(value)} < minLength {schema['minLength']}")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            raise ValidationError(path, f"String length {len(value)} > maxLength {schema['maxLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            raise ValidationError(path, f"String does not match pattern {schema['pattern']!r}")
        return

    # --- number / integer ---
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise ValidationError(path, f"Value {value} < minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            raise ValidationError(path, f"Value {value} > maximum {schema['maximum']}")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            raise ValidationError(path, f"Value {value} <= exclusiveMinimum {schema['exclusiveMinimum']}")
        if "exclusiveMaximum" in schema and value >= schema["exclusiveMaximum"]:
            raise ValidationError(path, f"Value {value} >= exclusiveMaximum {schema['exclusiveMaximum']}")
        if "multipleOf" in schema and value % schema["multipleOf"] != 0:
            raise ValidationError(path, f"Value {value} is not a multiple of {schema['multipleOf']}")
        return

    # --- array ---
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise ValidationError(path, f"Array length {len(value)} < minItems {schema['minItems']}")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ValidationError(path, f"Array length {len(value)} > maxItems {schema['maxItems']}")
        if "items" in schema:
            for i, item in enumerate(value):
                validate_json_schema(item, schema["items"], f"{path}[{i}]", definitions)
        return

    # --- object ---
    if isinstance(value, dict):
        props = schema.get("properties", {})
        required = schema.get("required", [])
        additional = schema.get("additionalProperties", True)

        for req in required:
            if req not in value:
                raise ValidationError(path, f"Missing required property '{req}'")

        for key, val in value.items():
            if key in props:
                validate_json_schema(val, props[key], f"{path}.{key}", definitions)
            elif additional is False:
                raise ValidationError(path, f"Additional property '{key}' not allowed")
            elif isinstance(additional, dict):
                validate_json_schema(val, additional, f"{path}.{key}", definitions)

        return


def _check_type(value: Any, expected: str | list[str], path: str) -> None:
    types = [expected] if isinstance(expected, str) else expected
    for t in types:
        if _matches_type(value, t):
            return
    raise ValidationError(path, f"Expected type {expected!r}, got {type(value).__name__}")


def _matches_type(value: Any, type_name: str) -> bool:
    if type_name == "null":
        return value is None
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "array":
        return isinstance(value, list)
    if type_name == "object":
        return isinstance(value, dict)
    return False
