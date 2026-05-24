"""
JSON Schema Validation Module for DataLens CLI.

Validates data against JSON Schema drafts (primarily draft-07 compatible).
Implements validation logic using only Python stdlib (no jsonschema dependency).

Supported validation keywords:
- type, enum, const
- required, properties, additionalProperties, patternProperties
- items, additionalItems, minItems, maxItems, uniqueItems
- minimum, maximum, exclusiveMinimum, exclusiveMaximum
- minLength, maxLength, pattern
- minProperties, maxProperties
- allOf, anyOf, oneOf, not
- $ref (simple resolution within the same schema)
- definitions / $defs
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union


class ValidationError(Exception):
    """Raised when data fails validation against a schema."""

    def __init__(self, message: str, path: str = "", value: Any = None):
        self.path = path
        self.value = value
        full = message
        if path:
            full = f"{message} (路径: {path})"
        super().__init__(full)


class ValidationResult:
    """Holds the result of a validation operation.

    Attributes:
        valid: Whether the data is valid.
        errors: List of validation error messages.
    """

    def __init__(self, valid: bool, errors: Optional[List[str]] = None):
        self.valid = valid
        self.errors = errors or []

    def __bool__(self) -> bool:
        return self.valid

    def __repr__(self) -> str:
        if self.valid:
            return "ValidationResult(valid=True)"
        return f"ValidationResult(valid=False, errors={len(self.errors)})"


def validate(data: Any, schema: Dict[str, Any]) -> ValidationResult:
    """Validate data against a JSON Schema.

    Args:
        data: The data to validate.
        schema: The JSON Schema dictionary.

    Returns:
        A ValidationResult with valid=True if data conforms, or valid=False
        with a list of error messages.
    """
    errors: List[str] = []
    _validate_node(data, schema, "", errors, schema)
    if errors:
        return ValidationResult(False, errors)
    return ValidationResult(True)


def validate_file(data_path: str, schema_path: str) -> ValidationResult:
    """Validate a data file against a schema file.

    Args:
        data_path: Path to the data file (JSON).
        schema_path: Path to the schema file (JSON).

    Returns:
        A ValidationResult.
    """
    import json
    from pathlib import Path

    data = json.loads(Path(data_path).read_text(encoding="utf-8"))
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    return validate(data, schema)


def _resolve_ref(
    schema: Dict[str, Any],
    root_schema: Dict[str, Any],
) -> Dict[str, Any]:
    """Resolve a $ref pointer within the schema.

    Supports simple JSON Pointer references (e.g., ``#/definitions/User``).

    Args:
        schema: The schema node containing the $ref.
        root_schema: The root schema for resolution.

    Returns:
        The resolved schema node.
    """
    ref = schema.get("$ref", "")
    if not ref.startswith("#/"):
        return schema

    parts = ref[2:].split("/")
    resolved = root_schema
    for part in parts:
        # Handle JSON Pointer escaping
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(resolved, dict) and part in resolved:
            resolved = resolved[part]
        else:
            return schema  # Cannot resolve, return as-is

    if isinstance(resolved, dict):
        return resolved
    return {"type": _json_type_name(resolved)}


def _json_type_name(value: Any) -> str:
    """Map a Python value to a JSON Schema type name.

    Args:
        value: A Python value.

    Returns:
        The JSON Schema type string.
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


def _check_type(value: Any, expected_type: str) -> bool:
    """Check if a value matches a JSON Schema type.

    Args:
        value: The value to check.
        expected_type: The expected JSON Schema type.

    Returns:
        True if the value matches the type.
    """
    if expected_type == "null":
        return value is None
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "object":
        return isinstance(value, dict)
    return False


def _validate_node(
    data: Any,
    schema: Dict[str, Any],
    path: str,
    errors: List[str],
    root_schema: Dict[str, Any],
) -> None:
    """Recursively validate a data node against a schema node.

    Args:
        data: The data to validate.
        schema: The schema to validate against.
        path: The current JSON path (for error messages).
        errors: Accumulator for error messages.
        root_schema: The root schema for $ref resolution.
    """
    if not schema or not isinstance(schema, dict):
        return

    # Resolve $ref
    if "$ref" in schema:
        resolved = _resolve_ref(schema, root_schema)
        _validate_node(data, resolved, path, errors, root_schema)
        return

    # Boolean schema (true = accept anything, false = reject everything)
    if isinstance(schema, bool):
        if not schema:
            errors.append(f"值被 schema(false) 拒绝 {path}")
        return

    # type
    if "type" in schema:
        expected = schema["type"]
        if isinstance(expected, list):
            if not any(_check_type(data, t) for t in expected):
                errors.append(
                    f"类型错误 {path}: 期望 {expected}, 实际为 {_json_type_name(data)}"
                )
        else:
            if not _check_type(data, expected):
                errors.append(
                    f"类型错误 {path}: 期望 '{expected}', 实际为 '{_json_type_name(data)}'"
                )

    # enum
    if "enum" in schema:
        if data not in schema["enum"]:
            errors.append(
                f"枚举值错误 {path}: 值 {repr(data)} 不在允许值列表中 "
                f"{schema['enum']}"
            )

    # const
    if "const" in schema:
        if data != schema["const"]:
            errors.append(
                f"常量值错误 {path}: 期望 {repr(schema['const'])}, 实际为 {repr(data)}"
            )

    # --- String validations ---
    if isinstance(data, str):
        if "minLength" in schema and len(data) < schema["minLength"]:
            errors.append(
                f"字符串太短 {path}: 长度 {len(data)} < 最小 {schema['minLength']}"
            )
        if "maxLength" in schema and len(data) > schema["maxLength"]:
            errors.append(
                f"字符串太长 {path}: 长度 {len(data)} > 最大 {schema['maxLength']}"
            )
        if "pattern" in schema:
            try:
                if not re.search(schema["pattern"], data):
                    errors.append(
                        f"模式不匹配 {path}: 值 '{data}' 不匹配模式 '{schema['pattern']}'"
                    )
            except re.error as e:
                errors.append(f"无效的正则模式 {path}: {e}")
        if "format" in schema:
            fmt = schema["format"]
            if fmt == "email" and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", data):
                errors.append(f"格式错误 {path}: '{data}' 不是有效的邮箱地址")
            elif fmt == "uri" and not re.match(r"^https?://", data):
                errors.append(f"格式错误 {path}: '{data}' 不是有效的 URI")
            elif fmt == "date-time" and not re.match(
                r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}", data
            ):
                errors.append(f"格式错误 {path}: '{data}' 不是有效的日期时间")

    # --- Number validations ---
    if isinstance(data, (int, float)) and not isinstance(data, bool):
        if "minimum" in schema and data < schema["minimum"]:
            errors.append(
                f"数值太小 {path}: {data} < 最小值 {schema['minimum']}"
            )
        if "maximum" in schema and data > schema["maximum"]:
            errors.append(
                f"数值太大 {path}: {data} > 最大值 {schema['maximum']}"
            )
        if "exclusiveMinimum" in schema and data <= schema["exclusiveMinimum"]:
            errors.append(
                f"数值不满足严格最小 {path}: {data} <= {schema['exclusiveMinimum']}"
            )
        if "exclusiveMaximum" in schema and data >= schema["exclusiveMaximum"]:
            errors.append(
                f"数值不满足严格最大 {path}: {data} >= {schema['exclusiveMaximum']}"
            )
        if "multipleOf" in schema:
            if schema["multipleOf"] != 0 and data % schema["multipleOf"] != 0:
                errors.append(
                    f"数值不是倍数 {path}: {data} 不是 {schema['multipleOf']} 的倍数"
                )

    # --- Array validations ---
    if isinstance(data, list):
        if "minItems" in schema and len(data) < schema["minItems"]:
            errors.append(
                f"数组元素太少 {path}: {len(data)} < 最少 {schema['minItems']}"
            )
        if "maxItems" in schema and len(data) > schema["maxItems"]:
            errors.append(
                f"数组元素太多 {path}: {len(data)} > 最多 {schema['maxItems']}"
            )
        if "uniqueItems" in schema and schema["uniqueItems"]:
            seen: List[Any] = []
            for item in data:
                if item in seen:
                    errors.append(f"数组包含重复元素 {path}: {repr(item)}")
                    break
                seen.append(item)

        if "items" in schema:
            items_schema = schema["items"]
            if isinstance(items_schema, dict):
                # All items must match the schema
                for i, item in enumerate(data):
                    _validate_node(
                        item, items_schema, f"{path}[{i}]", errors, root_schema
                    )
            elif isinstance(items_schema, list):
                # Tuple validation: each position has its own schema
                for i, item in enumerate(data):
                    if i < len(items_schema):
                        _validate_node(
                            item, items_schema[i], f"{path}[{i}]", errors, root_schema
                        )
                    elif schema.get("additionalItems", True) is False:
                        errors.append(
                            f"数组额外元素 {path}[{i}]: 不允许额外的数组元素"
                        )

        if "contains" in schema:
            found = False
            for item in data:
                test_errors: List[str] = []
                _validate_node(item, schema["contains"], path, test_errors, root_schema)
                if not test_errors:
                    found = True
                    break
            if not found:
                errors.append(f"数组不包含匹配项 {path}: 没有元素匹配 'contains' schema")

    # --- Object validations ---
    if isinstance(data, dict):
        if "required" in schema:
            for req_field in schema["required"]:
                if req_field not in data:
                    errors.append(f"缺少必填字段 {path}.{req_field}")

        if "minProperties" in schema and len(data) < schema["minProperties"]:
            errors.append(
                f"属性太少 {path}: {len(data)} < 最少 {schema['minProperties']}"
            )
        if "maxProperties" in schema and len(data) > schema["maxProperties"]:
            errors.append(
                f"属性太多 {path}: {len(data)} > 最多 {schema['maxProperties']}"
            )

        if "properties" in schema:
            for prop_name, prop_schema in schema["properties"].items():
                if prop_name in data:
                    _validate_node(
                        data[prop_name],
                        prop_schema,
                        f"{path}.{prop_name}",
                        errors,
                        root_schema,
                    )

        if "patternProperties" in schema:
            for pattern, prop_schema in schema["patternProperties"].items():
                try:
                    compiled = re.compile(pattern)
                except re.error:
                    continue
                for key, value in data.items():
                    if compiled.search(key):
                        _validate_node(
                            value, prop_schema, f"{path}.{key}", errors, root_schema
                        )

        if "additionalProperties" in schema:
            defined_props = set()
            if "properties" in schema:
                defined_props.update(schema["properties"].keys())
            if "patternProperties" in schema:
                for pattern in schema["patternProperties"]:
                    try:
                        compiled = re.compile(pattern)
                        for key in data:
                            if compiled.search(key):
                                defined_props.add(key)
                    except re.error:
                        continue

            additional = schema["additionalProperties"]
            for key in data:
                if key not in defined_props:
                    if additional is False:
                        errors.append(
                            f"不允许的额外属性 {path}.{key}"
                        )
                    elif isinstance(additional, dict):
                        _validate_node(
                            data[key], additional, f"{path}.{key}", errors, root_schema
                        )

        if "dependencies" in schema:
            for field, dep in schema["dependencies"].items():
                if field in data:
                    if isinstance(dep, list):
                        for d in dep:
                            if d not in data:
                                errors.append(
                                    f"依赖字段缺失 {path}: '{field}' 需要 '{d}'"
                                )
                    elif isinstance(dep, dict):
                        _validate_node(data, dep, path, errors, root_schema)

    # --- Composition keywords ---
    if "allOf" in schema:
        for i, sub_schema in enumerate(schema["allOf"]):
            _validate_node(data, sub_schema, path, errors, root_schema)

    if "anyOf" in schema:
        any_valid = False
        for sub_schema in schema["anyOf"]:
            test_errors: List[str] = []
            _validate_node(data, sub_schema, path, test_errors, root_schema)
            if not test_errors:
                any_valid = True
                break
        if not any_valid:
            errors.append(f"anyOf 验证失败 {path}: 没有任何子 schema 匹配")

    if "oneOf" in schema:
        match_count = 0
        for sub_schema in schema["oneOf"]:
            test_errors: List[str] = []
            _validate_node(data, sub_schema, path, test_errors, root_schema)
            if not test_errors:
                match_count += 1
        if match_count != 1:
            errors.append(
                f"oneOf 验证失败 {path}: 期望恰好 1 个匹配, 实际 {match_count} 个"
            )

    if "not" in schema:
        test_errors: List[str] = []
        _validate_node(data, schema["not"], path, test_errors, root_schema)
        if not test_errors:
            errors.append(f"not 验证失败 {path}: 值不应匹配 'not' schema")
