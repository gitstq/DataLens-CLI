"""
Pretty Print Module for DataLens CLI.

Provides syntax-highlighted pretty printing for JSON, YAML, TOML, and CSV data.
Uses ANSI color codes for terminal output (no external dependencies).
"""

import json
from typing import Any, Dict, List, Optional

from .utils import Colors, safe_colorize, serialize_yaml


# JSON syntax highlighting tokens
class JsonHighlighter:
    """ANSI-based JSON syntax highlighter."""

    # Color scheme
    KEY_COLOR = Colors.CYAN
    STRING_COLOR = Colors.GREEN
    NUMBER_COLOR = Colors.YELLOW
    BOOLEAN_COLOR = Colors.MAGENTA
    NULL_COLOR = Colors.RED
    BRACE_COLOR = Colors.WHITE
    BRACKET_COLOR = Colors.WHITE
    COLON_COLOR = Colors.WHITE
    COMMA_COLOR = Colors.WHITE

    @classmethod
    def highlight(cls, json_str: str, indent: int = 2) -> str:
        """Apply syntax highlighting to a JSON string.

        Args:
            json_str: The JSON string to highlight.
            indent: Indentation level (used for re-formatting).

        Returns:
            A colorized JSON string.
        """
        try:
            data = json.loads(json_str)
            formatted = json.dumps(data, indent=indent, ensure_ascii=False)
            return cls._colorize(formatted)
        except (json.JSONDecodeError, TypeError):
            return json_str

    @classmethod
    def highlight_data(cls, data: Any, indent: int = 2) -> str:
        """Apply syntax highlighting to Python data as JSON.

        Args:
            data: The data to highlight.
            indent: Indentation level.

        Returns:
            A colorized JSON string.
        """
        formatted = json.dumps(data, indent=indent, ensure_ascii=False, default=str)
        return cls._colorize(formatted)

    @classmethod
    def _colorize(cls, text: str) -> str:
        """Apply colors to a formatted JSON string.

        Uses a simple state-machine approach to identify and colorize tokens.

        Args:
            text: The formatted JSON string.

        Returns:
            The colorized string.
        """
        result: List[str] = []
        i = 0
        length = len(text)

        while i < length:
            ch = text[i]

            # Whitespace
            if ch in (" ", "\t", "\n", "\r"):
                result.append(ch)
                i += 1
                continue

            # String (key or value)
            if ch == '"':
                j = i + 1
                while j < length:
                    if text[j] == "\\" and j + 1 < length:
                        j += 2
                        continue
                    if text[j] == '"':
                        break
                    j += 1

                string_content = text[i:j + 1]

                # Determine if this is a key (followed by colon)
                k = j + 1
                while k < length and text[k] in (" ", "\t"):
                    k += 1

                if k < length and text[k] == ":":
                    # This is a key
                    result.append(safe_colorize(string_content, cls.KEY_COLOR))
                else:
                    # This is a string value
                    result.append(safe_colorize(string_content, cls.STRING_COLOR))

                i = j + 1
                continue

            # Number
            if ch in ("-", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"):
                j = i
                if text[j] == "-":
                    j += 1
                while j < length and text[j] in "0123456789":
                    j += 1
                if j < length and text[j] == ".":
                    j += 1
                    while j < length and text[j] in "0123456789":
                        j += 1
                if j < length and text[j] in ("e", "E"):
                    j += 1
                    if j < length and text[j] in ("+", "-"):
                        j += 1
                    while j < length and text[j] in "0123456789":
                        j += 1
                result.append(safe_colorize(text[i:j], cls.NUMBER_COLOR))
                i = j
                continue

            # Boolean
            if text[i:i + 4] == "true":
                result.append(safe_colorize("true", cls.BOOLEAN_COLOR))
                i += 4
                continue
            if text[i:i + 5] == "false":
                result.append(safe_colorize("false", cls.BOOLEAN_COLOR))
                i += 5
                continue

            # Null
            if text[i:i + 4] == "null":
                result.append(safe_colorize("null", cls.NULL_COLOR))
                i += 4
                continue

            # Structural characters
            if ch in ("{", "}"):
                result.append(safe_colorize(ch, cls.BRACE_COLOR))
                i += 1
                continue
            if ch in ("[", "]"):
                result.append(safe_colorize(ch, cls.BRACKET_COLOR))
                i += 1
                continue
            if ch == ":":
                result.append(safe_colorize(": ", cls.COLON_COLOR))
                i += 1
                # Skip space after colon
                if i < length and text[i] == " ":
                    i += 1
                continue
            if ch == ",":
                result.append(safe_colorize(",", cls.COMMA_COLOR))
                i += 1
                continue

            # Any other character
            result.append(ch)
            i += 1

        return "".join(result)


def pretty_print(
    data: Any,
    indent: int = 2,
    color: bool = True,
    format_type: str = "json",
) -> str:
    """Pretty print data with optional syntax highlighting.

    Args:
        data: The data to pretty print.
        indent: Indentation level.
        color: Whether to use color output.
        format_type: Output format ('json', 'yaml', 'toml', 'csv').

    Returns:
        A formatted string.
    """
    if format_type in ("yaml", "yml"):
        return _pretty_yaml(data, indent)

    if format_type == "toml":
        return _pretty_toml(data)

    if format_type == "csv":
        return _pretty_csv(data)

    # Default: JSON
    if color:
        return JsonHighlighter.highlight_data(data, indent=indent)
    else:
        return json.dumps(data, indent=indent, ensure_ascii=False, default=str)


def _pretty_yaml(data: Any, indent: int = 2) -> str:
    """Pretty print data as YAML.

    Args:
        data: The data to format.
        indent: Indentation level.

    Returns:
        YAML formatted string.
    """
    try:
        return serialize_yaml(data)
    except Exception:
        # Fallback to JSON
        return json.dumps(data, indent=indent, ensure_ascii=False, default=str)


def _pretty_toml(data: Any) -> str:
    """Pretty print data as TOML.

    Args:
        data: The data to format.

    Returns:
        TOML formatted string.
    """
    from .utils import serialize_toml
    try:
        return serialize_toml(data)
    except Exception:
        # Fallback to JSON
        return json.dumps(data, indent=2, ensure_ascii=False, default=str)


def _pretty_csv(data: Any) -> str:
    """Pretty print data as a formatted table.

    Args:
        data: The data to format (list of dicts).

    Returns:
        A table-formatted string.
    """
    if not isinstance(data, list):
        data = [data]
    if not data:
        return "(empty)"

    # Collect headers
    headers: List[str] = []
    seen: set = set()
    for row in data:
        if isinstance(row, dict):
            for key in row:
                if key not in seen:
                    headers.append(str(key))
                    seen.add(key)

    if not headers:
        return "\n".join(str(item) for item in data)

    # Calculate column widths
    rows: List[List[str]] = []
    for row in data:
        if isinstance(row, dict):
            rows.append([str(row.get(h, "")) for h in headers])
        else:
            rows.append([str(row)])

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(cell))

    # Build table
    lines: List[str] = []

    # Header
    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    lines.append(header_line)

    # Separator
    sep_line = "-+-".join("-" * col_widths[i] for i in range(len(headers)))
    lines.append(sep_line)

    # Rows
    for row in rows:
        row_line = " | ".join(
            cell.ljust(col_widths[i]) if i < len(col_widths) else cell
            for i, cell in enumerate(row)
        )
        lines.append(row_line)

    return "\n".join(lines)


def print_data(
    data: Any,
    indent: int = 2,
    color: Optional[bool] = None,
    format_type: str = "json",
) -> None:
    """Print data to stdout with optional syntax highlighting.

    Args:
        data: The data to print.
        indent: Indentation level.
        color: Whether to use color (auto-detect if None).
        format_type: Output format.
    """
    if color is None:
        from .utils import supports_color
        color = supports_color()

    output = pretty_print(data, indent=indent, color=color, format_type=format_type)
    print(output)
