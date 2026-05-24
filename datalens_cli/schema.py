"""
Schema Inference Module for DataLens CLI.

Automatically generates JSON Schema from sample data.
Detects types, required fields, enums, patterns, and nested structures.
"""

import re
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple, Union


def infer_schema(
    data: Any,
    title: Optional[str] = None,
    root: bool = True,
) -> Dict[str, Any]:
    """Infer a JSON Schema from sample data.

    Analyzes the data structure and generates a comprehensive JSON Schema
    that describes the types, required fields, enums, and constraints.

    Args:
        data: The sample data to analyze.
        title: Optional title for the schema.
        root: Whether this is the root schema (adds $schema).

    Returns:
        A JSON Schema dictionary.
    """
    schema: Dict[str, Any] = {}

    if root:
        schema["$schema"] = "http://json-schema.org/draft-07/schema#"
        if title:
            schema["title"] = title

    _infer_type(schema, data)

    if title and root:
        schema["title"] = title

    return schema


def infer_schema_from_file(file_path: str, title: Optional[str] = None) -> Dict[str, Any]:
    """Infer a JSON Schema from a data file.

    Args:
        file_path: Path to the data file.
        title: Optional title for the schema.

    Returns:
        A JSON Schema dictionary.
    """
    from .utils import read_file

    data = read_file(file_path)
    return infer_schema(data, title=title)


def _infer_type(schema: Dict[str, Any], data: Any) -> None:
    """Infer the type and constraints for a value, updating the schema in-place.

    Args:
        schema: The schema dictionary to update.
        data: The data to analyze.
    """
    if data is None:
        schema["type"] = "null"

    elif isinstance(data, bool):
        schema["type"] = "boolean"

    elif isinstance(data, int):
        schema["type"] = "integer"

    elif isinstance(data, float):
        schema["type"] = "number"

    elif isinstance(data, str):
        _infer_string(schema, data)

    elif isinstance(data, list):
        _infer_array(schema, data)

    elif isinstance(data, dict):
        _infer_object(schema, data)

    else:
        schema["type"] = "string"


def _infer_string(schema: Dict[str, Any], value: str) -> None:
    """Infer string-specific constraints.

    Args:
        schema: The schema dictionary to update.
        value: The string value to analyze.
    """
    schema["type"] = "string"

    # Detect format
    if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
        schema["format"] = "email"
    elif re.match(r"^https?://", value):
        schema["format"] = "uri"
    elif re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        schema["format"] = "date"
    elif re.match(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}", value):
        schema["format"] = "date-time"
    elif re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", value.lower()):
        schema["format"] = "uuid"


def _infer_array(schema: Dict[str, Any], data: List[Any]) -> None:
    """Infer array-specific constraints.

    Args:
        schema: The schema dictionary to update.
        data: The list to analyze.
    """
    schema["type"] = "array"

    if not data:
        return

    # Check for unique items
    if len(data) == len(set(repr(item) for item in data)):
        schema["uniqueItems"] = True

    # Analyze item types
    item_types = Counter()
    for item in data:
        item_types[_get_base_type(item)] += 1

    if len(item_types) == 1:
        # All items have the same type
        item_schema: Dict[str, Any] = {}
        _infer_type(item_schema, data[0])

        # If there are multiple items, check for additional constraints
        if len(data) > 1:
            _infer_from_multiple_values(item_schema, data)

        schema["items"] = item_schema
    elif len(item_types) <= 3:
        # Mixed types - use tuple validation or anyOf
        type_schemas = []
        seen_types: Set[str] = set()
        for item in data:
            base = _get_base_type(item)
            if base not in seen_types:
                seen_types.add(base)
                s: Dict[str, Any] = {}
                _infer_type(s, item)
                type_schemas.append(s)

        if len(type_schemas) == 1:
            schema["items"] = type_schemas[0]
        else:
            schema["items"] = {"anyOf": type_schemas}
    else:
        # Too many types, just note it's an array
        pass


def _infer_object(schema: Dict[str, Any], data: Dict[str, Any]) -> None:
    """Infer object-specific constraints.

    Args:
        schema: The schema dictionary to update.
        data: The dict to analyze.
    """
    schema["type"] = "object"

    if not data:
        return

    properties: Dict[str, Any] = {}
    required: List[str] = []

    for key, value in data.items():
        prop_schema: Dict[str, Any] = {}
        _infer_type(prop_schema, value)
        properties[key] = prop_schema
        required.append(key)

    schema["properties"] = properties
    schema["required"] = required
    schema["additionalProperties"] = True


def _infer_from_multiple_values(schema: Dict[str, Any], values: List[Any]) -> None:
    """Infer additional constraints from multiple values of the same type.

    Detects enums (when all values are from a small set), min/max for numbers,
    min/max length for strings, etc.

    Args:
        schema: The schema dictionary to update.
        values: List of values to analyze.
    """
    if not values:
        return

    # Check for enum (small set of distinct values)
    # Use repr-based dedup to handle unhashable types
    seen_reprs: set = set()
    unique_values = []
    for v in values:
        r = repr(v)
        if r not in seen_reprs:
            seen_reprs.add(r)
            unique_values.append(v)
    if len(unique_values) <= 5 and len(unique_values) < len(values):
        # All values are from a small set - use enum
        if all(isinstance(v, (str, int, float, bool)) or v is None for v in unique_values):
            schema["enum"] = sorted(unique_values, key=lambda x: (x is None, x))
            return

    # String constraints
    if all(isinstance(v, str) for v in values):
        lengths = [len(v) for v in values]
        if len(set(lengths)) == 1:
            schema["minLength"] = lengths[0]
            schema["maxLength"] = lengths[0]
        else:
            schema["minLength"] = min(lengths)
            schema["maxLength"] = max(lengths)

        # Check for common patterns
        patterns = [_detect_pattern(v) for v in values]
        if all(p is not None for p in patterns) and len(set(patterns)) == 1:
            schema["pattern"] = patterns[0]

    # Number constraints
    if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
        schema["minimum"] = min(values)
        schema["maximum"] = max(values)

        # Check for multipleOf
        if all(isinstance(v, int) for v in values):
            if len(values) > 1:
                diffs = [abs(values[i + 1] - values[i]) for i in range(len(values) - 1)]
                if len(set(diffs)) == 1 and diffs[0] > 0:
                    schema["multipleOf"] = diffs[0]


def _detect_pattern(value: str) -> Optional[str]:
    """Detect a regex pattern that describes a string value.

    Args:
        value: The string to analyze.

    Returns:
        A regex pattern string, or None if no pattern is detected.
    """
    if re.match(r"^\d+$", value):
        return r"^\d+$"
    if re.match(r"^[a-zA-Z]+$", value):
        return r"^[a-zA-Z]+$"
    if re.match(r"^[a-zA-Z0-9]+$", value):
        return r"^[a-zA-Z0-9]+$"
    if re.match(r"^[a-z]+-[a-z]+$", value):
        return r"^[a-z]+-[a-z]+$"
    if re.match(r"^[A-Z][a-z]+$", value):
        return r"^[A-Z][a-z]+$"
    return None


def _get_base_type(value: Any) -> str:
    """Get the base JSON type name for a value.

    Args:
        value: Any Python value.

    Returns:
        The JSON type name string.
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "string"


def merge_schemas(schemas: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge multiple JSON Schemas into a single combined schema.

    The merged schema uses allOf to combine the schemas, and also attempts
    to merge compatible properties directly.

    Args:
        schemas: List of JSON Schema dictionaries to merge.

    Returns:
        A merged JSON Schema dictionary.
    """
    if not schemas:
        return {}
    if len(schemas) == 1:
        return schemas[0]

    # Try direct merge for object schemas
    all_objects = all(s.get("type") == "object" for s in schemas if "type" in s)
    if all_objects:
        merged: Dict[str, Any] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {},
            "required": [],
        }

        all_required: Set[str] = set()
        for schema in schemas:
            props = schema.get("properties", {})
            merged["properties"].update(props)
            req = set(schema.get("required", []))
            all_required.update(req)

        merged["required"] = sorted(all_required)
        merged["additionalProperties"] = True
        return merged

    # Fall back to allOf
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "allOf": schemas,
    }
