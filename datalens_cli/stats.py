"""
Data Statistics Module for DataLens CLI.

Analyzes data structures and produces statistics including field counts,
type distributions, nesting depth, size metrics, and more.
"""

from collections import Counter
from typing import Any, Dict, List, Optional, Tuple, Union

from .utils import Colors, safe_colorize


class DataStats:
    """Statistics about a data structure.

    Attributes:
        root_type: The type of the root element.
        total_keys: Total number of keys in all nested objects.
        total_items: Total number of items in all arrays.
        max_depth: Maximum nesting depth.
        type_distribution: Counter of value types encountered.
        field_info: Detailed information about each field.
        size_bytes: Approximate size in bytes (JSON serialized).
    """

    def __init__(self):
        self.root_type: str = ""
        self.total_keys: int = 0
        self.total_items: int = 0
        self.max_depth: int = 0
        self.type_distribution: Counter = Counter()
        self.field_info: Dict[str, Dict[str, Any]] = {}
        self.size_bytes: int = 0
        self.array_lengths: List[int] = []
        self.null_count: int = 0
        self.empty_string_count: int = 0
        self.string_lengths: List[int] = []
        self.number_values: List[Union[int, float]] = []

    def summary(self, use_color: bool = True) -> str:
        """Generate a human-readable summary of the statistics.

        Args:
            use_color: Whether to use ANSI color codes.

        Returns:
            A formatted summary string.
        """
        lines: List[str] = []

        # Header
        title = safe_colorize("数据统计报告", Colors.BOLD + Colors.CYAN) if use_color \
            else "数据统计报告"
        lines.append(title)
        lines.append("=" * 50)
        lines.append("")

        # Root type
        type_str = safe_colorize(self.root_type, Colors.GREEN) if use_color else self.root_type
        lines.append(f"根类型:           {type_str}")

        # Size
        size_str = _format_size(self.size_bytes)
        lines.append(f"数据大小:         {size_str}")

        # Depth
        lines.append(f"最大嵌套深度:     {self.max_depth}")

        # Counts
        lines.append(f"对象键总数:       {self.total_keys}")
        lines.append(f"数组元素总数:     {self.total_items}")
        lines.append(f"空值 (null) 数量: {self.null_count}")
        lines.append(f"空字符串数量:     {self.empty_string_count}")

        lines.append("")

        # Type distribution
        type_header = safe_colorize("类型分布:", Colors.BOLD) if use_color else "类型分布:"
        lines.append(type_header)
        for type_name, count in self.type_distribution.most_common():
            bar = _build_bar(count, max(self.type_distribution.values()) if self.type_distribution else 1)
            if use_color:
                bar = safe_colorize(bar, Colors.CYAN)
            lines.append(f"  {type_name:<12} {count:>6}  {bar}")

        lines.append("")

        # String stats
        if self.string_lengths:
            avg_len = sum(self.string_lengths) / len(self.string_lengths)
            lines.append(f"字符串统计:")
            lines.append(f"  数量:       {len(self.string_lengths)}")
            lines.append(f"  平均长度:   {avg_len:.1f}")
            lines.append(f"  最短:       {min(self.string_lengths)}")
            lines.append(f"  最长:       {max(self.string_lengths)}")
            lines.append("")

        # Number stats
        if self.number_values:
            lines.append(f"数值统计:")
            lines.append(f"  数量:       {len(self.number_values)}")
            lines.append(f"  最小值:     {min(self.number_values)}")
            lines.append(f"  最大值:     {max(self.number_values)}")
            if len(self.number_values) > 1:
                avg = sum(self.number_values) / len(self.number_values)
                lines.append(f"  平均值:     {avg:.2f}")
            lines.append("")

        # Array stats
        if self.array_lengths:
            avg_len = sum(self.array_lengths) / len(self.array_lengths)
            lines.append(f"数组统计:")
            lines.append(f"  数量:       {len(self.array_lengths)}")
            lines.append(f"  平均长度:   {avg_len:.1f}")
            lines.append(f"  最短:       {min(self.array_lengths)}")
            lines.append(f"  最长:       {max(self.array_lengths)}")
            lines.append("")

        # Field details (for objects)
        if self.field_info:
            field_header = safe_colorize("字段详情:", Colors.BOLD) if use_color else "字段详情:"
            lines.append(field_header)
            for field_name, info in sorted(self.field_info.items()):
                type_str = info.get("type", "unknown")
                if use_color:
                    type_str = safe_colorize(type_str, Colors.YELLOW)
                required = "必填" if info.get("required", False) else "可选"
                null_pct = info.get("null_percentage", 0)
                lines.append(
                    f"  {field_name:<25} {type_str:<10} {required:<6} "
                    f"空值率: {null_pct:.0f}%"
                )

        return "\n".join(lines)


def compute_stats(data: Any) -> DataStats:
    """Compute statistics for a data structure.

    Args:
        data: The data to analyze.

    Returns:
        A DataStats object with computed statistics.
    """
    stats = DataStats()
    stats.root_type = _get_type_name(data)

    # Compute approximate size
    import json
    try:
        stats.size_bytes = len(json.dumps(data, ensure_ascii=False, default=str))
    except (TypeError, ValueError):
        stats.size_bytes = len(repr(data))

    # Analyze structure
    _analyze(data, stats, depth=0, path="$", is_required=True)

    return stats


def compute_stats_file(file_path: str) -> DataStats:
    """Compute statistics for a data file.

    Args:
        file_path: Path to the data file.

    Returns:
        A DataStats object.
    """
    from .utils import read_file
    data = read_file(file_path)
    return compute_stats(data)


def _analyze(
    data: Any,
    stats: DataStats,
    depth: int,
    path: str,
    is_required: bool = True,
) -> None:
    """Recursively analyze a data structure.

    Args:
        data: The current data node.
        stats: The stats object to update.
        depth: Current nesting depth.
        path: Current JSON path.
        is_required: Whether this field is always present.
    """
    # Update max depth
    if depth > stats.max_depth:
        stats.max_depth = depth

    type_name = _get_type_name(data)
    stats.type_distribution[type_name] += 1

    if data is None:
        stats.null_count += 1

    elif isinstance(data, bool):
        pass  # Already counted in type distribution

    elif isinstance(data, (int, float)):
        stats.number_values.append(data)

    elif isinstance(data, str):
        if data == "":
            stats.empty_string_count += 1
        stats.string_lengths.append(len(data))

    elif isinstance(data, list):
        stats.array_lengths.append(len(data))
        stats.total_items += len(data)
        for i, item in enumerate(data):
            _analyze(item, stats, depth + 1, f"{path}[{i}]", is_required)

    elif isinstance(data, dict):
        stats.total_keys += len(data)
        for key, value in data.items():
            field_path = f"{path}.{key}"

            # Update field info
            if key not in stats.field_info:
                stats.field_info[key] = {
                    "type": _get_type_name(value),
                    "count": 0,
                    "null_count": 0,
                    "required": is_required,
                    "null_percentage": 0.0,
                }

            stats.field_info[key]["count"] += 1
            if value is None:
                stats.field_info[key]["null_count"] += 1

            # Calculate null percentage
            info = stats.field_info[key]
            if info["count"] > 0:
                info["null_percentage"] = (info["null_count"] / info["count"]) * 100

            # Update type if we see a different type
            current_type = _get_type_name(value)
            if info["type"] != current_type:
                if "types" not in info:
                    info["types"] = {info["type"]}
                info["types"].add(current_type)
                # Use union type description
                type_list = sorted(info["types"])
                if len(type_list) <= 3:
                    info["type"] = "|".join(type_list)
                else:
                    info["type"] = "mixed"

            _analyze(value, stats, depth + 1, field_path, is_required)


def _get_type_name(value: Any) -> str:
    """Get a JSON-compatible type name for a value.

    Args:
        value: Any Python value.

    Returns:
        The type name string.
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
    return type(value).__name__


def _format_size(size_bytes: int) -> str:
    """Format a byte size as a human-readable string.

    Args:
        size_bytes: Size in bytes.

    Returns:
        Formatted size string.
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def _build_bar(count: int, max_count: int, width: int = 20) -> str:
    """Build a text-based bar chart.

    Args:
        count: The count for this bar.
        max_count: The maximum count (for scaling).
        width: Maximum bar width in characters.

    Returns:
        A string of block characters.
    """
    if max_count == 0:
        return ""
    filled = int((count / max_count) * width)
    return "\u2588" * filled + "\u2591" * (width - filled)
