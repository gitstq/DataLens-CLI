"""
Deep Merge Module for DataLens CLI.

Provides deep merge functionality for combining multiple data structures.
Supports custom merge strategies and conflict resolution.
"""

from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union


class MergeConflictError(Exception):
    """Raised when a merge encounters an unresolvable conflict."""

    def __init__(self, message: str, path: str = "", value1: Any = None, value2: Any = None):
        self.path = path
        self.value1 = value1
        self.value2 = value2
        full = message
        if path:
            full = f"{message} (路径: {path})"
        super().__init__(full)


def deep_merge(base: Any, *overrides: Any, strategy: str = "overwrite") -> Any:
    """Deep merge multiple data structures.

    Merges overrides into the base data structure. Dictionaries are merged
    recursively. Lists can be merged with different strategies.

    Args:
        base: The base data structure.
        *overrides: One or more override data structures to merge into base.
        strategy: Merge strategy for conflicts:
            - "overwrite": Override values replace base values (default)
            - "append": Lists are concatenated
            - "prepend": Override list items are prepended
            - "unique": Lists are merged with unique items only
            - "deep": Attempt to merge list items by index

    Returns:
        The merged data structure.

    Raises:
        MergeConflictError: If conflicts cannot be resolved.
    """
    result = _deep_copy(base)

    for override in overrides:
        result = _merge_two(result, override, "$", strategy)

    return result


def merge_files(file_paths: List[str], strategy: str = "overwrite") -> Any:
    """Merge multiple data files.

    Args:
        file_paths: List of file paths to merge.
        strategy: Merge strategy.

    Returns:
        The merged data structure.
    """
    from .utils import read_file

    if not file_paths:
        return {}

    result = read_file(file_paths[0])

    for path in file_paths[1:]:
        override = read_file(path)
        result = _merge_two(result, override, "$", strategy)

    return result


def _merge_two(base: Any, override: Any, path: str, strategy: str) -> Any:
    """Merge two values according to the specified strategy.

    Args:
        base: The base value.
        override: The override value.
        path: Current path for error reporting.
        strategy: The merge strategy.

    Returns:
        The merged value.
    """
    # If override is None, keep base
    if override is None:
        return base

    # If base is None, use override
    if base is None:
        return override

    # Both are dicts - merge recursively
    if isinstance(base, dict) and isinstance(override, dict):
        return _merge_dicts(base, override, path, strategy)

    # Both are lists - merge according to strategy
    if isinstance(base, list) and isinstance(override, list):
        return _merge_lists(base, override, path, strategy)

    # Type mismatch or scalar - override wins
    return override


def _merge_dicts(
    base: Dict[str, Any],
    override: Dict[str, Any],
    path: str,
    strategy: str,
) -> Dict[str, Any]:
    """Deep merge two dictionaries.

    Args:
        base: The base dictionary.
        override: The override dictionary.
        path: Current path.
        strategy: Merge strategy.

    Returns:
        A new merged dictionary.
    """
    result = dict(base)

    for key, value in override.items():
        new_path = f"{path}.{key}"
        if key in result:
            result[key] = _merge_two(result[key], value, new_path, strategy)
        else:
            result[key] = _deep_copy(value)

    return result


def _merge_lists(
    base: List[Any],
    override: List[Any],
    path: str,
    strategy: str,
) -> List[Any]:
    """Merge two lists according to the specified strategy.

    Args:
        base: The base list.
        override: The override list.
        path: Current path.
        strategy: Merge strategy.

    Returns:
        A new merged list.
    """
    if strategy == "overwrite":
        return list(override)

    elif strategy == "append":
        return base + [_deep_copy(item) for item in override]

    elif strategy == "prepend":
        return [_deep_copy(item) for item in override] + base

    elif strategy == "unique":
        seen: List[Any] = list(base)
        for item in override:
            if item not in seen:
                seen.append(_deep_copy(item))
        return seen

    elif strategy == "deep":
        # Merge by index - extend base if override is longer
        result = list(base)
        for i, item in enumerate(override):
            if i < len(result):
                result[i] = _merge_two(result[i], item, f"{path}[{i}]", strategy)
            else:
                result.append(_deep_copy(item))
        return result

    else:
        return list(override)


def _deep_copy(value: Any) -> Any:
    """Create a deep copy of a value without using the copy module.

    Handles dicts, lists, and primitive types.

    Args:
        value: The value to copy.

    Returns:
        A deep copy of the value.
    """
    if isinstance(value, dict):
        return {k: _deep_copy(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_deep_copy(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_deep_copy(item) for item in value)
    if isinstance(value, set):
        return {_deep_copy(item) for item in value}
    return value


def flatten(data: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
    """Flatten a nested dictionary.

    Args:
        data: The nested dictionary to flatten.
        separator: The separator to use between levels.

    Returns:
        A flattened dictionary with dot-notation keys.
    """
    result: Dict[str, Any] = {}

    def _flatten(obj: Any, prefix: str = "") -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_key = f"{prefix}{separator}{key}" if prefix else key
                if isinstance(value, (dict, list)):
                    _flatten(value, new_key)
                else:
                    result[new_key] = value
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_key = f"{prefix}[{i}]"
                if isinstance(item, (dict, list)):
                    _flatten(item, new_key)
                else:
                    result[new_key] = item
        else:
            result[prefix] = obj

    _flatten(data)
    return result


def unflatten(data: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
    """Unflatten a dictionary with dot-notation keys.

    Args:
        data: The flattened dictionary.
        separator: The separator used in keys.

    Returns:
        A nested dictionary.
    """
    result: Dict[str, Any] = {}

    for key, value in data.items():
        parts = key.split(separator)
        current = result

        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    return result
