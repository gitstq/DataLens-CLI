"""
Deep Data Comparison (Diff) Module for DataLens CLI.

Compares two JSON/YAML data structures and produces a detailed diff report
showing additions, deletions, and changes with color-coded output.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from .utils import Colors, safe_colorize


class DiffResult:
    """Represents the result of a diff operation.

    Attributes:
        added: List of paths that were added.
        removed: List of paths that were removed.
        changed: List of (path, old_value, new_value) tuples.
        unchanged: Count of unchanged paths.
        is_identical: Whether the two structures are identical.
    """

    def __init__(
        self,
        added: Optional[List[str]] = None,
        removed: Optional[List[str]] = None,
        changed: Optional[List[Tuple[str, Any, Any]]] = None,
        unchanged: int = 0,
    ):
        self.added = added or []
        self.removed = removed or []
        self.changed = changed or []
        self.unchanged = unchanged
        self.is_identical = not self.added and not self.removed and not self.changed

    def __repr__(self) -> str:
        return (
            f"DiffResult(added={len(self.added)}, "
            f"removed={len(self.removed)}, "
            f"changed={len(self.changed)}, "
            f"unchanged={self.unchanged})"
        )

    def summary(self) -> str:
        """Generate a human-readable summary of the diff.

        Returns:
            A summary string.
        """
        parts = []
        if self.is_identical:
            return "两个数据结构完全相同"

        if self.added:
            parts.append(f"{len(self.added)} 个新增")
        if self.removed:
            parts.append(f"{len(self.removed)} 个删除")
        if self.changed:
            parts.append(f"{len(self.changed)} 个修改")

        return "差异: " + ", ".join(parts)


def diff(data1: Any, data2: Any, path: str = "$") -> DiffResult:
    """Compute a deep diff between two data structures.

    Args:
        data1: The first (original) data structure.
        data2: The second (modified) data structure.
        path: The current path (used in recursion).

    Returns:
        A DiffResult containing all differences.
    """
    added: List[str] = []
    removed: List[str] = []
    changed: List[Tuple[str, Any, Any]] = []
    unchanged = 0

    # Both are None
    if data1 is None and data2 is None:
        return DiffResult(unchanged=1)

    # One is None
    if data1 is None:
        added.append(path)
        return DiffResult(added=added)
    if data2 is None:
        removed.append(path)
        return DiffResult(removed=removed)

    # Type mismatch
    type1 = type(data1).__name__
    type2 = type(data2).__name__
    if type1 != type2:
        changed.append((path, data1, data2))
        return DiffResult(changed=changed)

    # Both are dicts
    if isinstance(data1, dict) and isinstance(data2, dict):
        return _diff_dicts(data1, data2, path)

    # Both are lists
    if isinstance(data1, list) and isinstance(data2, list):
        return _diff_lists(data1, data2, path)

    # Scalar comparison
    if data1 != data2:
        changed.append((path, data1, data2))
    else:
        unchanged = 1

    return DiffResult(added=added, removed=removed, changed=changed, unchanged=unchanged)


def diff_files(file1: str, file2: str) -> DiffResult:
    """Compute a diff between two data files.

    Args:
        file1: Path to the first file.
        file2: Path to the second file.

    Returns:
        A DiffResult.
    """
    from .utils import read_file

    data1 = read_file(file1)
    data2 = read_file(file2)
    return diff(data1, data2)


def _diff_dicts(
    dict1: Dict[str, Any],
    dict2: Dict[str, Any],
    path: str,
) -> DiffResult:
    """Diff two dictionaries.

    Args:
        dict1: The first dictionary.
        dict2: The second dictionary.
        path: The current path.

    Returns:
        A DiffResult for the dictionary comparison.
    """
    added: List[str] = []
    removed: List[str] = []
    changed: List[Tuple[str, Any, Any]] = []
    unchanged = 0

    keys1 = set(dict1.keys())
    keys2 = set(dict2.keys())

    # Keys only in dict2 (added)
    for key in sorted(keys2 - keys1):
        added.append(f"{path}.{key}")

    # Keys only in dict1 (removed)
    for key in sorted(keys1 - keys2):
        removed.append(f"{path}.{key}")

    # Keys in both (compare recursively)
    for key in sorted(keys1 & keys2):
        sub_result = diff(dict1[key], dict2[key], f"{path}.{key}")
        added.extend(sub_result.added)
        removed.extend(sub_result.removed)
        changed.extend(sub_result.changed)
        unchanged += sub_result.unchanged

    return DiffResult(added=added, removed=removed, changed=changed, unchanged=unchanged)


def _diff_lists(
    list1: List[Any],
    list2: List[Any],
    path: str,
) -> DiffResult:
    """Diff two lists.

    Compares items by position. For lists of dicts, attempts key-based matching.

    Args:
        list1: The first list.
        list2: The second list.
        path: The current path.

    Returns:
        A DiffResult for the list comparison.
    """
    added: List[str] = []
    removed: List[str] = []
    changed: List[Tuple[str, Any, Any]] = []
    unchanged = 0

    # Try key-based matching for lists of dicts
    if list1 and list2 and all(isinstance(item, dict) for item in list1) and \
       all(isinstance(item, dict) for item in list2):
        return _diff_list_of_dicts(list1, list2, path)

    # Position-based comparison
    max_len = max(len(list1), len(list2))

    for i in range(max_len):
        item_path = f"{path}[{i}]"
        if i >= len(list1):
            added.append(item_path)
        elif i >= len(list2):
            removed.append(item_path)
        else:
            sub_result = diff(list1[i], list2[i], item_path)
            added.extend(sub_result.added)
            removed.extend(sub_result.removed)
            changed.extend(sub_result.changed)
            unchanged += sub_result.unchanged

    return DiffResult(added=added, removed=removed, changed=changed, unchanged=unchanged)


def _diff_list_of_dicts(
    list1: List[Dict[str, Any]],
    list2: List[Dict[str, Any]],
    path: str,
) -> DiffResult:
    """Diff two lists of dicts using key-based matching.

    Attempts to find a unique key (like 'id', 'name') to match items between lists.

    Args:
        list1: The first list of dicts.
        list2: The second list of dicts.
        path: The current path.

    Returns:
        A DiffResult.
    """
    added: List[str] = []
    removed: List[str] = []
    changed: List[Tuple[str, Any, Any]] = []
    unchanged = 0

    # Find a matching key
    match_key = _find_match_key(list1, list2)

    if match_key is None:
        # Fall back to position-based
        return _diff_lists(list1, list2, path)

    # Build index by match_key
    map1: Dict[Any, Dict[str, Any]] = {}
    map2: Dict[Any, Dict[str, Any]] = {}

    for item in list1:
        key_val = item.get(match_key)
        if key_val is not None:
            map1[key_val] = item

    for item in list2:
        key_val = item.get(match_key)
        if key_val is not None:
            map2[key_val] = item

    keys1 = set(map1.keys())
    keys2 = set(map2.keys())

    # Added items
    for key in sorted(keys2 - keys1):
        added.append(f"{path}[{match_key}={key!r}]")

    # Removed items
    for key in sorted(keys1 - keys2):
        removed.append(f"{path}[{match_key}={key!r}]")

    # Changed items
    for key in sorted(keys1 & keys2):
        item_path = f"{path}[{match_key}={key!r}]"
        sub_result = diff(map1[key], map2[key], item_path)
        added.extend(sub_result.added)
        removed.extend(sub_result.removed)
        changed.extend(sub_result.changed)
        unchanged += sub_result.unchanged

    return DiffResult(added=added, removed=removed, changed=changed, unchanged=unchanged)


def _find_match_key(
    list1: List[Dict[str, Any]],
    list2: List[Dict[str, Any]],
) -> Optional[str]:
    """Find a unique key that can be used to match items between two lists of dicts.

    Looks for common keys where all values are unique in both lists.

    Args:
        list1: First list of dicts.
        list2: Second list of dicts.

    Returns:
        The name of a suitable matching key, or None.
    """
    common_keys = set(list1[0].keys()) & set(list2[0].keys()) if list1 and list2 else set()

    # Priority order for matching keys
    priority_keys = ["id", "ID", "Id", "key", "Key", "name", "Name", "slug", "uuid"]

    for key in priority_keys:
        if key in common_keys:
            vals1 = [item.get(key) for item in list1 if key in item]
            vals2 = [item.get(key) for item in list2 if key in item]
            if len(vals1) == len(set(vals1)) and len(vals2) == len(set(vals2)):
                return key

    # Try any common key
    for key in common_keys:
        vals1 = [item.get(key) for item in list1 if key in item]
        vals2 = [item.get(key) for item in list2 if key in item]
        if len(vals1) == len(set(vals1)) and len(vals2) == len(set(vals2)) and \
           len(vals1) > 0 and len(vals2) > 0:
            return key

    return None


def format_diff(result: DiffResult, use_color: bool = True) -> str:
    """Format a DiffResult as a human-readable, color-coded string.

    Args:
        result: The diff result to format.
        use_color: Whether to use ANSI color codes.

    Returns:
        A formatted string representation of the diff.
    """
    lines: List[str] = []

    if result.is_identical:
        msg = "两个数据结构完全相同"
        if use_color:
            msg = safe_colorize(msg, Colors.GREEN)
        lines.append(msg)
        return "\n".join(lines)

    # Summary
    summary = result.summary()
    if use_color:
        summary = safe_colorize(summary, Colors.BOLD)
    lines.append(summary)
    lines.append("")

    # Added
    if result.added:
        header = safe_colorize(f"[+] 新增 ({len(result.added)})", Colors.GREEN) if use_color \
            else f"[+] 新增 ({len(result.added)})"
        lines.append(header)
        for path in result.added:
            prefix = safe_colorize("  + ", Colors.GREEN) if use_color else "  + "
            lines.append(f"{prefix}{path}")
        lines.append("")

    # Removed
    if result.removed:
        header = safe_colorize(f"[-] 删除 ({len(result.removed)})", Colors.RED) if use_color \
            else f"[-] 删除 ({len(result.removed)})"
        lines.append(header)
        for path in result.removed:
            prefix = safe_colorize("  - ", Colors.RED) if use_color else "  - "
            lines.append(f"{prefix}{path}")
        lines.append("")

    # Changed
    if result.changed:
        header = safe_colorize(f"[~] 修改 ({len(result.changed)})", Colors.YELLOW) if use_color \
            else f"[~] 修改 ({len(result.changed)})"
        lines.append(header)
        for path, old_val, new_val in result.changed:
            if use_color:
                lines.append(f"  {safe_colorize('~', Colors.YELLOW)} {path}")
                lines.append(f"    {safe_colorize(f'- {format_value(old_val)}', Colors.RED)}")
                lines.append(f"    {safe_colorize(f'+ {format_value(new_val)}', Colors.GREEN)}")
            else:
                lines.append(f"  ~ {path}")
                lines.append(f"    - {format_value(old_val)}")
                lines.append(f"    + {format_value(new_val)}")
        lines.append("")

    return "\n".join(lines)


def format_value(value: Any, max_length: int = 80) -> str:
    """Format a value for display in diff output.

    Args:
        value: The value to format.
        max_length: Maximum length for string representation.

    Returns:
        A formatted string.
    """
    import json

    try:
        s = json.dumps(value, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        s = str(value)

    if len(s) > max_length:
        s = s[:max_length - 3] + "..."
    return s
