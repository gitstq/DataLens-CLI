"""
Filter and Sort Module for DataLens CLI.

Provides data filtering and sorting operations for lists of records.
Supports multiple filter conditions, sorting by multiple fields,
and various comparison operators.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from .utils import DataLensError


class FilterError(DataLensError):
    """Raised when a filter operation fails."""

    pass


def filter_data(
    data: List[Dict[str, Any]],
    conditions: Optional[List[Dict[str, Any]]] = None,
    field: Optional[str] = None,
    op: Optional[str] = None,
    value: Any = None,
) -> List[Dict[str, Any]]:
    """Filter a list of records based on conditions.

    Can accept either a list of condition dicts or individual field/op/value args.

    Args:
        data: The list of records to filter.
        conditions: List of condition dicts with keys: field, op, value.
        field: Field name (alternative to conditions).
        op: Comparison operator (alternative to conditions).
        value: Comparison value (alternative to conditions).

    Returns:
        A filtered list of records.

    Raises:
        FilterError: If the filter specification is invalid.
    """
    if not isinstance(data, list):
        raise FilterError("过滤操作要求数据为列表 (list)")

    if not data:
        return []

    # Build conditions list from individual args
    if conditions is None:
        if field is None:
            raise FilterError("必须指定过滤条件 (--field, --op, --value)")
        conditions = [{"field": field, "op": op or "==", "value": value}]

    result = data
    for condition in conditions:
        result = _apply_filter(result, condition)

    return result


def sort_data(
    data: List[Dict[str, Any]],
    fields: Optional[List[str]] = None,
    field: Optional[str] = None,
    reverse: bool = False,
) -> List[Dict[str, Any]]:
    """Sort a list of records by one or more fields.

    Args:
        data: The list of records to sort.
        fields: List of field names to sort by (prefix with '-' for descending).
        field: Single field name (alternative to fields).
        reverse: Reverse sort order (only used with single field).

    Returns:
        A sorted list of records.

    Raises:
        FilterError: If the sort specification is invalid.
    """
    if not isinstance(data, list):
        raise FilterError("排序操作要求数据为列表 (list)")

    if not data:
        return []

    if fields is None:
        if field is None:
            raise FilterError("必须指定排序字段 (--field 或 --sort)")
        fields = [field]

    # Parse sort specifications
    sort_specs: List[Tuple[str, bool]] = []
    for f in fields:
        if f.startswith("-"):
            sort_specs.append((f[1:], True))
        elif f.startswith("+"):
            sort_specs.append((f[1:], False))
        else:
            sort_specs.append((f, reverse))

    def sort_key(record: Dict[str, Any]) -> tuple:
        """Create a sort key tuple for a record."""
        key_parts: List[Any] = []
        for field_name, desc in sort_specs:
            val = record.get(field_name)
            # Handle None values (sort to end)
            if val is None:
                key_parts.append((1, ""))
            elif isinstance(val, (int, float)):
                key_parts.append((0, val))
            else:
                key_parts.append((0, str(val)))
        return tuple(key_parts)

    result = sorted(data, key=sort_key)

    # Apply per-field reverse
    for field_name, desc in reversed(sort_specs):
        if desc:
            result = sorted(
                result,
                key=lambda r: (r.get(field_name) is None, r.get(field_name, "")),
                reverse=True,
            )

    return result


def _apply_filter(
    data: List[Dict[str, Any]],
    condition: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Apply a single filter condition to data.

    Args:
        data: The list of records.
        condition: A dict with 'field', 'op', and 'value' keys.

    Returns:
        Filtered list of records.
    """
    field = condition.get("field", "")
    op = condition.get("op", "==")
    value = condition.get("value")

    if not field:
        raise FilterError("过滤条件缺少 'field' 字段")

    result = []
    for record in data:
        if not isinstance(record, dict):
            continue

        # Support nested field access with dot notation
        record_value = _get_nested_value(record, field)

        if _compare_values(record_value, op, value):
            result.append(record)

    return result


def _get_nested_value(record: Dict[str, Any], field: str) -> Any:
    """Get a value from a record using dot notation.

    Args:
        record: The record dictionary.
        field: Dot-notation field path (e.g., 'address.city').

    Returns:
        The value at the specified path, or None.
    """
    parts = field.split(".")
    current: Any = record

    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None

        if current is None:
            return None

    return current


def _compare_values(actual: Any, op: str, expected: Any) -> bool:
    """Compare two values using the specified operator.

    Supported operators:
        ==, !=, >, <, >=, <=, contains, !contains,
        starts, ends, in, !in, regex, type, exists, !exists

    Args:
        actual: The actual value from the data.
        op: The comparison operator.
        expected: The expected value.

    Returns:
        True if the comparison matches.
    """
    try:
        if op == "==" or op == "eq":
            return actual == expected
        elif op == "!=" or op == "ne":
            return actual != expected
        elif op == ">" or op == "gt":
            return _safe_compare(actual, expected, lambda a, b: a > b)
        elif op == "<" or op == "lt":
            return _safe_compare(actual, expected, lambda a, b: a < b)
        elif op == ">=" or op == "ge":
            return _safe_compare(actual, expected, lambda a, b: a >= b)
        elif op == "<=" or op == "le":
            return _safe_compare(actual, expected, lambda a, b: a <= b)
        elif op == "contains":
            if isinstance(actual, str) and isinstance(expected, str):
                return expected in actual
            if isinstance(actual, (list, tuple)):
                return expected in actual
            return False
        elif op == "!contains":
            if isinstance(actual, str) and isinstance(expected, str):
                return expected not in actual
            if isinstance(actual, (list, tuple)):
                return expected not in actual
            return True
        elif op == "starts" or op == "startswith":
            return isinstance(actual, str) and actual.startswith(str(expected))
        elif op == "ends" or op == "endswith":
            return isinstance(actual, str) and actual.endswith(str(expected))
        elif op == "in":
            return actual in expected if isinstance(expected, (list, tuple)) else False
        elif op == "!in":
            return actual not in expected if isinstance(expected, (list, tuple)) else True
        elif op == "regex" or op == "=~":
            import re
            if isinstance(actual, str):
                return bool(re.search(str(expected), actual))
            return False
        elif op == "type":
            return type(actual).__name__ == str(expected)
        elif op == "exists":
            return actual is not None
        elif op == "!exists":
            return actual is None
        else:
            raise FilterError(f"不支持的比较运算符: '{op}'")
    except (TypeError, ValueError):
        return False


def _safe_compare(actual: Any, expected: Any, cmp_func: Callable[[Any, Any], bool]) -> bool:
    """Safely compare two values, handling type mismatches.

    Args:
        actual: The actual value.
        expected: The expected value.
        cmp_func: The comparison function.

    Returns:
        The result of the comparison, or False if types are incompatible.
    """
    if actual is None or expected is None:
        return False
    try:
        return cmp_func(actual, expected)
    except TypeError:
        return False


def unique(data: List[Dict[str, Any]], field: Optional[str] = None) -> List[Dict[str, Any]]:
    """Remove duplicate records from a list.

    Args:
        data: The list of records.
        field: If specified, deduplicate by this field only.

    Returns:
        A list with duplicates removed.
    """
    if not data:
        return []

    if field:
        seen: set = set()
        result = []
        for record in data:
            key = record.get(field)
            if key not in seen:
                seen.add(key)
                result.append(record)
        return result
    else:
        # Deduplicate by full record content
        seen: List[str] = []
        result = []
        for record in data:
            key = repr(_make_hashable(record))
            if key not in seen:
                seen.append(key)
                result.append(record)
        return result


def _make_hashable(value: Any) -> Any:
    """Convert a value to a hashable form for comparison.

    Args:
        value: The value to convert.

    Returns:
        A hashable representation.
    """
    if isinstance(value, dict):
        return tuple(sorted((k, _make_hashable(v)) for k, v in value.items()))
    if isinstance(value, list):
        return tuple(_make_hashable(v) for v in value)
    return value


def limit(data: List[Any], count: int, offset: int = 0) -> List[Any]:
    """Limit the number of results with an optional offset.

    Args:
        data: The list to limit.
        count: Maximum number of items to return.
        offset: Number of items to skip.

    Returns:
        A sliced list.
    """
    return data[offset:offset + count]


def select_fields(
    data: List[Dict[str, Any]],
    fields: List[str],
) -> List[Dict[str, Any]]:
    """Select only specific fields from each record.

    Args:
        data: The list of records.
        fields: List of field names to keep.

    Returns:
        A list of records with only the selected fields.
    """
    result = []
    for record in data:
        if isinstance(record, dict):
            new_record = {}
            for field in fields:
                value = _get_nested_value(record, field)
                # Use the last part of the field path as the key
                key = field.split(".")[-1]
                new_record[key] = value
            result.append(new_record)
        else:
            result.append(record)
    return result
