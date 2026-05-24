"""
Smart Query Engine for DataLens CLI.

Supports multiple query expression formats:
- Dot notation: ``a.b.c``
- Array indexing: ``a[0]``, ``a[-1]``
- Wildcard: ``a[*]``, ``a[*].name``
- Recursive descent: ``a..b``
- JSONPath-like filter expressions: ``a[?b>5]``
- Root selector: ``$`` or ``.``

Examples:
    >>> query(data, "users[0].name")
    >>> query(data, "store..price")
    >>> query(data, "$.users[*].email")
    >>> query(data, "items[?price>100]")
"""

import re
from typing import Any, List, Optional, Tuple, Union


class QueryError(Exception):
    """Raised when a query expression is invalid or cannot be evaluated."""

    def __init__(self, message: str, expression: str = "", details: str = ""):
        self.expression = expression
        self.details = details
        full = message
        if expression:
            full = f"{message} (表达式: '{expression}')"
        if details:
            full = f"{full} - {details}"
        super().__init__(full)


def query(data: Any, expression: str) -> Any:
    """Execute a query expression against data.

    This is the main entry point for the query engine. It parses the expression
    and evaluates it against the provided data.

    Args:
        data: The data to query (dict, list, or scalar).
        expression: The query expression string.

    Returns:
        The queried result. Can be a scalar, list, dict, or None.

    Raises:
        QueryError: If the expression is invalid or evaluation fails.
    """
    if not expression or expression.strip() in ("", ".", "$"):
        return data

    expression = expression.strip()

    # Remove leading $ if present
    if expression.startswith("$"):
        expression = expression[1:]
    # Remove single leading . (but preserve .. for recursive descent)
    if expression.startswith(".") and not expression.startswith(".."):
        expression = expression[1:]

    tokens = _tokenize(expression)
    return _evaluate_tokens(data, tokens, expression)


def _tokenize(expression: str) -> List[str]:
    """Tokenize a query expression into path segments.

    Handles dot-separated keys, array indices, wildcards, and recursive descent.

    Args:
        expression: The query expression string (without leading $ or .).

    Returns:
        A list of token strings.

    Raises:
        QueryError: If the expression syntax is invalid.
    """
    tokens: List[str] = []
    i = 0
    length = len(expression)

    while i < length:
        ch = expression[i]

        # Recursive descent operator ..
        if ch == "." and i + 1 < length and expression[i + 1] == ".":
            tokens.append("..")
            i += 2
            continue

        # Dot separator
        if ch == ".":
            i += 1
            continue

        # Array index or filter: [...]
        if ch == "[":
            # Find matching ]
            depth = 1
            j = i + 1
            while j < length and depth > 0:
                if expression[j] == "[":
                    depth += 1
                elif expression[j] == "]":
                    depth -= 1
                j += 1

            if depth != 0:
                raise QueryError("未闭合的方括号", expression)

            bracket_content = expression[i + 1 : j - 1]
            tokens.append(f"[{bracket_content}]")
            i = j

            # Skip dot after bracket if present
            if i < length and expression[i] == ".":
                i += 1
            continue

        # Regular key - read until . or [
        j = i
        while j < length and expression[j] not in (".", "["):
            j += 1

        key = expression[i:j]
        if key:
            tokens.append(key)
        i = j

    return tokens


def _evaluate_tokens(data: Any, tokens: List[str], expression: str) -> Any:
    """Evaluate a list of tokens against data.

    Args:
        data: The current data context.
        tokens: The list of tokens to evaluate.
        expression: The original expression (for error messages).

    Returns:
        The result of evaluating all tokens.

    Raises:
        QueryError: If a token cannot be evaluated.
    """
    current = data

    for idx, token in enumerate(tokens):
        if current is None:
            return None

        if token == "..":
            # Recursive descent - collect all matching values from all levels
            remaining_tokens = tokens[idx + 1 :]
            if not remaining_tokens:
                raise QueryError("递归下降运算符 '..' 后缺少路径段", expression)
            return _recursive_descent(current, remaining_tokens, expression)

        if token.startswith("[") and token.endswith("]"):
            inner = token[1:-1].strip()

            if inner == "*":
                # Wildcard array index
                if isinstance(current, list):
                    results = []
                    remaining = tokens[idx + 1 :]
                    for item in current:
                        if remaining:
                            results.append(
                                _evaluate_tokens(item, remaining, expression)
                            )
                        else:
                            results.append(item)
                    return results
                elif isinstance(current, dict):
                    # Wildcard on dict means all values
                    results = []
                    remaining = tokens[idx + 1 :]
                    for value in current.values():
                        if remaining:
                            results.append(
                                _evaluate_tokens(value, remaining, expression)
                            )
                        else:
                            results.append(value)
                    return results
                else:
                    return None

            if inner.startswith("?"):
                # Filter expression: [?field>value]
                current = _evaluate_filter(current, inner[1:], expression)
                continue

            # Array index
            try:
                index = int(inner)
            except ValueError:
                raise QueryError(
                    f"无效的数组索引: '{inner}'",
                    expression,
                    "索引必须是整数或 '*' 或过滤表达式"
                )

            if isinstance(current, list):
                try:
                    current = current[index]
                except IndexError:
                    return None
            elif isinstance(current, dict) and str(index) in current:
                current = current[str(index)]
            else:
                return None
        else:
            # Dictionary key access
            if isinstance(current, dict):
                if token in current:
                    current = current[token]
                else:
                    return None
            elif isinstance(current, list):
                # Try to interpret as integer index
                try:
                    index = int(token)
                    current = current[index]
                except (ValueError, IndexError):
                    return None
            else:
                return None

    return current


def _recursive_descent(data: Any, remaining_tokens: List[str], expression: str) -> List[Any]:
    """Perform recursive descent, searching all nested levels.

    Args:
        data: The current data to search.
        remaining_tokens: Tokens after the .. operator.
        expression: The original expression.

    Returns:
        A list of all matching values found at any nesting level.
    """
    results: List[Any] = []

    def _search(obj: Any) -> None:
        """Recursively search through the data structure."""
        if obj is None:
            return

        # Try to match remaining tokens at this level
        try:
            match = _evaluate_tokens(obj, remaining_tokens, expression)
            if match is not None:
                if isinstance(match, list) and not remaining_tokens[0].startswith("["):
                    # Flatten single-level results
                    results.extend(match)
                else:
                    results.append(match)
        except (QueryError, KeyError, IndexError, TypeError):
            pass

        # Recurse into nested structures
        if isinstance(obj, dict):
            for value in obj.values():
                _search(value)
        elif isinstance(obj, list):
            for item in obj:
                _search(item)

    _search(data)
    return results


def _evaluate_filter(data: Any, filter_expr: str, expression: str) -> List[Any]:
    """Evaluate a filter expression against a list.

    Supports comparison operators: ==, !=, >, <, >=, <=, =~ (regex match)

    Args:
        data: The data to filter (should be a list).
        filter_expr: The filter expression (e.g., ``price>100``, ``name=~John``).
        expression: The original expression for error messages.

    Returns:
        A filtered list of items.

    Raises:
        QueryError: If the filter syntax is invalid.
    """
    if not isinstance(data, list):
        raise QueryError("过滤表达式只能应用于数组", expression)

    # Parse the filter expression
    # Supported patterns:
    #   field==value, field!=value, field>value, field<value, field>=value, field<=value
    #   field=~pattern (regex match)
    #   !field (existence check - items that have this field)
    filter_expr = filter_expr.strip()

    # Negation / existence check
    # !field means "items that do NOT have this field"
    if filter_expr.startswith("!"):
        field = filter_expr[1:].strip()
        return [item for item in data if isinstance(item, dict) and field not in item]

    # Regex match
    regex_match = re.match(r"^(\w+)\s*=~\s*(.+)$", filter_expr)
    if regex_match:
        field = regex_match.group(1)
        pattern = regex_match.group(2).strip().strip("'\"")
        try:
            compiled = re.compile(pattern)
        except re.error as e:
            raise QueryError(f"无效的正则表达式: {pattern}", expression, str(e))
        return [
            item for item in data
            if isinstance(item, dict)
            and field in item
            and isinstance(item[field], str)
            and compiled.search(item[field])
        ]

    # Comparison operators
    operators = [">=", "<=", "!=", "==", ">", "<"]
    for op in operators:
        # Find the operator, but be careful with == vs =
        idx = filter_expr.find(op)
        if idx != -1:
            field = filter_expr[:idx].strip()
            value_str = filter_expr[idx + len(op):].strip()
            value = _parse_filter_value(value_str)
            return [
                item for item in data
                if isinstance(item, dict)
                and field in item
                and _compare(item[field], op, value)
            ]

    # Simple field existence (just a field name)
    field = filter_expr.strip()
    return [item for item in data if isinstance(item, dict) and field in item]


def _parse_filter_value(value_str: str) -> Any:
    """Parse a filter value string into a Python value.

    Handles quoted strings, numbers, booleans, and null.

    Args:
        value_str: The value string from a filter expression.

    Returns:
        The parsed Python value.
    """
    # Quoted string
    if (value_str.startswith('"') and value_str.endswith('"')) or \
       (value_str.startswith("'") and value_str.endswith("'")):
        return value_str[1:-1]

    # Boolean
    if value_str.lower() == "true":
        return True
    if value_str.lower() == "false":
        return False

    # Null
    if value_str.lower() == "null" or value_str.lower() == "none":
        return None

    # Number
    try:
        if "." in value_str:
            return float(value_str)
        return int(value_str)
    except ValueError:
        pass

    # Return as string
    return value_str


def _compare(actual: Any, op: str, expected: Any) -> bool:
    """Compare two values using the specified operator.

    Args:
        actual: The actual value from the data.
        op: The comparison operator.
        expected: The expected value from the filter expression.

    Returns:
        True if the comparison matches, False otherwise.
    """
    try:
        if op == "==":
            return actual == expected
        elif op == "!=":
            return actual != expected
        elif op == ">":
            return actual > expected
        elif op == "<":
            return actual < expected
        elif op == ">=":
            return actual >= expected
        elif op == "<=":
            return actual <= expected
    except TypeError:
        return False
    return False


def query_all(data: Any, expression: str) -> List[Any]:
    """Query data and always return a list of results.

    Unlike query(), this function always returns a list, making it useful
    for batch operations where you need to iterate over results.

    Args:
        data: The data to query.
        expression: The query expression string.

    Returns:
        A list of matching values.
    """
    result = query(data, expression)
    if result is None:
        return []
    if isinstance(result, list):
        return result
    return [result]


def has_path(data: Any, expression: str) -> bool:
    """Check if a path exists in the data.

    Args:
        data: The data to check.
        expression: The query expression string.

    Returns:
        True if the path exists and resolves to a non-None value.
    """
    try:
        result = query(data, expression)
        return result is not None
    except QueryError:
        return False


def set_value(data: dict, expression: str, value: Any) -> dict:
    """Set a value at a given path in the data.

    Creates intermediate dictionaries as needed.

    Args:
        data: The data dictionary to modify.
        expression: The dot-notation path to set.
        value: The value to set.

    Returns:
        The modified data dictionary.
    """
    tokens = _tokenize(expression)
    current = data

    for i, token in enumerate(tokens):
        is_last = i == len(tokens) - 1

        if token.startswith("[") and token.endswith("]"):
            inner = token[1:-1].strip()
            try:
                index = int(inner)
            except ValueError:
                raise QueryError(f"set_value 不支持复杂表达式: {token}")

            if not isinstance(current, list):
                raise QueryError(f"路径段 '{token}' 需要数组，但当前值是 {type(current).__name__}")

            while len(current) <= index:
                current.append(None)

            if is_last:
                current[index] = value
            else:
                if current[index] is None:
                    next_token = tokens[i + 1]
                    if next_token.startswith("["):
                        current[index] = []
                    else:
                        current[index] = {}
                current = current[index]
        else:
            if is_last:
                current[token] = value
            else:
                if token not in current or current[token] is None:
                    next_token = tokens[i + 1]
                    if next_token.startswith("["):
                        current[token] = []
                    else:
                        current[token] = {}
                current = current[token]

    return data


def delete_path(data: dict, expression: str) -> dict:
    """Delete a value at a given path in the data.

    Args:
        data: The data dictionary to modify.
        expression: The dot-notation path to delete.

    Returns:
        The modified data dictionary.

    Raises:
        QueryError: If the path does not exist.
    """
    tokens = _tokenize(expression)
    if not tokens:
        raise QueryError("删除路径不能为空")

    current = data

    # Navigate to the parent
    for token in tokens[:-1]:
        if isinstance(current, dict):
            if token not in current:
                raise QueryError(f"路径不存在: {expression}")
            current = current[token]
        elif isinstance(current, list):
            try:
                current = current[int(token)]
            except (ValueError, IndexError):
                raise QueryError(f"路径不存在: {expression}")
        else:
            raise QueryError(f"路径不存在: {expression}")

    # Delete the last key
    last_token = tokens[-1]
    if last_token.startswith("[") and last_token.endswith("]"):
        inner = last_token[1:-1].strip()
        try:
            index = int(inner)
            if isinstance(current, list):
                del current[index]
            elif isinstance(current, dict):
                del current[str(index)]
            else:
                raise QueryError(f"路径不存在: {expression}")
        except (ValueError, IndexError):
            raise QueryError(f"路径不存在: {expression}")
    else:
        if isinstance(current, dict) and last_token in current:
            del current[last_token]
        else:
            raise QueryError(f"路径不存在: {expression}")

    return data
