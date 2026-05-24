"""
Shared utilities for DataLens CLI.

Provides common helper functions used across all modules, including:
- File I/O operations (read/write with format auto-detection)
- ANSI color codes for terminal output
- Type checking and conversion helpers
- Error handling utilities
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


# ---------------------------------------------------------------------------
# ANSI Color Codes
# ---------------------------------------------------------------------------

class Colors:
    """ANSI color escape codes for terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"

    # Bright foreground colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"

    # Background colors
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"


def colorize(text: str, color: str) -> str:
    """Wrap text with an ANSI color code.

    Args:
        text: The text to colorize.
        color: An ANSI escape code string from the Colors class.

    Returns:
        The colorized text string.
    """
    return f"{color}{text}{Colors.RESET}"


def supports_color() -> bool:
    """Check if the current terminal supports color output.

    Returns:
        True if the terminal supports ANSI colors, False otherwise.
    """
    if sys.platform == "win32":
        return True  # Windows 10+ supports ANSI via API
    if not hasattr(sys.stdout, "isatty"):
        return False
    if not sys.stdout.isatty():
        return False
    return True


def safe_colorize(text: str, color: str) -> str:
    """Colorize text only if the terminal supports colors.

    Args:
        text: The text to colorize.
        color: An ANSI escape code string.

    Returns:
        The colorized text if colors are supported, otherwise plain text.
    """
    if supports_color():
        return colorize(text, color)
    return text


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

class DataLensError(Exception):
    """Base exception for all DataLens CLI errors."""

    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        full = message
        if details:
            full = f"{message}: {details}"
        super().__init__(full)


class FileNotFoundError_(DataLensError):
    """Raised when a specified file cannot be found."""

    pass


class FileFormatError(DataLensError):
    """Raised when a file format is not recognized or cannot be parsed."""

    pass


class FormatNotSupportedError(DataLensError):
    """Raised when a requested format is not supported."""

    pass


def detect_format(file_path: Union[str, Path]) -> str:
    """Detect the data format of a file based on its extension.

    Args:
        file_path: Path to the file.

    Returns:
        Lowercase format string: 'json', 'yaml', 'yml', 'toml', or 'csv'.

    Raises:
        FileFormatError: If the file extension is not recognized.
    """
    ext = Path(file_path).suffix.lower()
    format_map = {
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yml",
        ".toml": "toml",
        ".csv": "csv",
    }
    if ext not in format_map:
        raise FileFormatError(
            f"无法识别文件格式 '{ext}'",
            f"支持的格式: {', '.join(format_map.keys())}"
        )
    return format_map[ext]


def read_file(file_path: Union[str, Path]) -> Any:
    """Read and parse a data file, auto-detecting its format.

    Supports JSON, YAML (requires pyyaml), TOML (requires toml), and CSV.

    Args:
        file_path: Path to the file to read.

    Returns:
        Parsed data as a Python object (dict, list, etc.).

    Raises:
        FileNotFoundError_: If the file does not exist.
        FileFormatError: If the file cannot be parsed.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError_(f"文件不存在: {file_path}")

    fmt = detect_format(file_path)
    content = path.read_text(encoding="utf-8")

    if fmt == "json":
        return parse_json(content)
    elif fmt in ("yaml", "yml"):
        return parse_yaml(content)
    elif fmt == "toml":
        return parse_toml(content)
    elif fmt == "csv":
        return parse_csv(content)
    else:
        raise FileFormatError(f"不支持的格式: {fmt}")


def read_stdin() -> Tuple[Any, str]:
    """Read data from stdin and attempt to detect its format.

    Returns:
        A tuple of (parsed_data, format_string).

    Raises:
        FileFormatError: If the stdin data cannot be parsed.
    """
    content = sys.stdin.read()
    if not content.strip():
        raise DataLensError("stdin 为空，没有可处理的数据")

    # Try JSON first
    try:
        data = parse_json(content)
        return data, "json"
    except (json.JSONDecodeError, DataLensError):
        pass

    # Try YAML
    try:
        data = parse_yaml(content)
        return data, "yaml"
    except DataLensError:
        pass

    # Try TOML
    try:
        data = parse_toml(content)
        return data, "toml"
    except DataLensError:
        pass

    # Try CSV
    try:
        data = parse_csv(content)
        return data, "csv"
    except DataLensError:
        pass

    raise FileFormatError("无法自动检测 stdin 数据格式，请指定格式")


def parse_json(content: str) -> Any:
    """Parse a JSON string.

    Args:
        content: JSON string to parse.

    Returns:
        Parsed Python object.

    Raises:
        FileFormatError: If the JSON is invalid.
    """
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise FileFormatError(f"JSON 解析失败: {e}")


def parse_yaml(content: str) -> Any:
    """Parse a YAML string. Requires pyyaml.

    Args:
        content: YAML string to parse.

    Returns:
        Parsed Python object.

    Raises:
        DataLensError: If pyyaml is not installed.
        FileFormatError: If the YAML is invalid.
    """
    try:
        import yaml
    except ImportError:
        raise DataLensError(
            "YAML 支持需要安装 pyyaml 库",
            "请运行: pip install pyyaml"
        )
    try:
        return yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise FileFormatError(f"YAML 解析失败: {e}")


def parse_toml(content: str) -> Any:
    """Parse a TOML string. Requires toml library.

    Args:
        content: TOML string to parse.

    Returns:
        Parsed Python object (dict).

    Raises:
        DataLensError: If toml library is not installed.
        FileFormatError: If the TOML is invalid.
    """
    # Python 3.11+ has tomllib in stdlib
    if sys.version_info >= (3, 11):
        import tomllib
        try:
            return tomllib.loads(content)
        except Exception as e:
            raise FileFormatError(f"TOML 解析失败: {e}")

    try:
        import toml
    except ImportError:
        raise DataLensError(
            "TOML 支持需要安装 toml 库 (Python < 3.11)",
            "请运行: pip install toml"
        )
    try:
        return toml.loads(content)
    except Exception as e:
        raise FileFormatError(f"TOML 解析失败: {e}")


def parse_csv(content: str) -> List[Dict[str, Any]]:
    """Parse a CSV string into a list of dictionaries.

    The first row is treated as headers.

    Args:
        content: CSV string to parse.

    Returns:
        List of dicts, where each dict maps column headers to values.

    Raises:
        FileFormatError: If the CSV is invalid.
    """
    import csv as csv_module
    import io

    try:
        reader = csv_module.DictReader(io.StringIO(content))
        result = []
        for row in reader:
            # Convert numeric strings to numbers where possible
            converted = {}
            for key, value in row.items():
                converted[key] = _convert_csv_value(value)
            result.append(converted)
        return result
    except Exception as e:
        raise FileFormatError(f"CSV 解析失败: {e}")


def _convert_csv_value(value: str) -> Any:
    """Attempt to convert a CSV string value to an appropriate Python type.

    Args:
        value: The string value from a CSV cell.

    Returns:
        The converted value (int, float, bool, or original string).
    """
    if value is None:
        return None
    stripped = value.strip()
    if stripped == "":
        return None

    # Boolean detection
    if stripped.lower() in ("true", "yes", "1"):
        return True
    if stripped.lower() in ("false", "no", "0"):
        # Only treat as boolean if it matches exactly
        if stripped.lower() in ("true", "yes"):
            return True
        if stripped.lower() in ("false", "no"):
            return False

    # Integer detection
    try:
        return int(stripped)
    except ValueError:
        pass

    # Float detection
    try:
        return float(stripped)
    except ValueError:
        pass

    return value


def write_file(
    file_path: Union[str, Path],
    data: Any,
    fmt: Optional[str] = None,
    indent: int = 2,
) -> None:
    """Write data to a file in the specified format.

    Args:
        file_path: Path to the output file.
        data: The data to write.
        fmt: Output format. If None, detected from file extension.
        indent: Indentation level for JSON output.

    Raises:
        FileFormatError: If the format is not supported or data cannot be serialized.
    """
    path = Path(file_path)
    if fmt is None:
        fmt = detect_format(file_path)

    if fmt == "json":
        content = serialize_json(data, indent=indent)
    elif fmt in ("yaml", "yml"):
        content = serialize_yaml(data)
    elif fmt == "toml":
        content = serialize_toml(data)
    elif fmt == "csv":
        content = serialize_csv(data)
    else:
        raise FormatNotSupportedError(f"不支持的输出格式: {fmt}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def serialize_json(data: Any, indent: int = 2) -> str:
    """Serialize data to a JSON string.

    Args:
        data: The data to serialize.
        indent: Number of spaces for indentation.

    Returns:
        JSON formatted string.
    """
    return json.dumps(data, indent=indent, ensure_ascii=False, default=str)


def serialize_yaml(data: Any) -> str:
    """Serialize data to a YAML string. Requires pyyaml.

    Args:
        data: The data to serialize.

    Returns:
        YAML formatted string.

    Raises:
        DataLensError: If pyyaml is not installed.
    """
    try:
        import yaml
    except ImportError:
        raise DataLensError(
            "YAML 输出需要安装 pyyaml 库",
            "请运行: pip install pyyaml"
        )
    return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)


def serialize_toml(data: Any) -> str:
    """Serialize data to a TOML string. Requires toml library.

    Args:
        data: The data to serialize (must be a dict).

    Returns:
        TOML formatted string.

    Raises:
        DataLensError: If toml library is not installed or data is not a dict.
    """
    if not isinstance(data, dict):
        raise DataLensError("TOML 格式仅支持顶层字典 (dict) 数据")

    if sys.version_info >= (3, 11):
        import tomllib  # noqa: F811 - tomllib only has loads, not dumps
        # Python 3.11+ tomllib is read-only, fall back to toml package for writing
        try:
            import toml
            return toml.dumps(data)
        except ImportError:
            raise DataLensError(
                "TOML 输出需要安装 toml 库",
                "请运行: pip install toml"
            )

    try:
        import toml
    except ImportError:
        raise DataLensError(
            "TOML 输出需要安装 toml 库",
            "请运行: pip install toml"
        )
    return toml.dumps(data)


def serialize_csv(data: Any) -> str:
    """Serialize data to a CSV string.

    Expects a list of dicts. Nested objects are flattened using dot notation.

    Args:
        data: The data to serialize (list of dicts).

    Returns:
        CSV formatted string.

    Raises:
        DataLensError: If data is not a list of dicts.
    """
    import csv as csv_module
    import io

    if not isinstance(data, list):
        raise DataLensError("CSV 格式要求数据为列表 (list)")

    if not data:
        return ""

    # Flatten nested dicts
    flat_rows = [_flatten_dict(row) for row in data]

    # Collect all headers preserving order
    headers: List[str] = []
    seen: set = set()
    for row in flat_rows:
        for key in row.keys():
            if key not in seen:
                headers.append(key)
                seen.add(key)

    output = io.StringIO()
    writer = csv_module.DictWriter(output, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    for row in flat_rows:
        writer.writerow(row)

    return output.getvalue()


def _flatten_dict(
    d: Dict[str, Any],
    parent_key: str = "",
    sep: str = ".",
) -> Dict[str, Any]:
    """Flatten a nested dictionary using dot notation for keys.

    Args:
        d: The dictionary to flatten.
        parent_key: Prefix for keys (used in recursion).
        sep: Separator between key levels.

    Returns:
        A flattened dictionary.
    """
    items: List[Tuple[str, Any]] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep).items())
        elif isinstance(v, list):
            # Convert list to string representation for CSV
            items.append((new_key, json.dumps(v, ensure_ascii=False)))
        else:
            items.append((new_key, v))
    return dict(items)


# ---------------------------------------------------------------------------
# Type Helpers
# ---------------------------------------------------------------------------

def get_type_name(value: Any) -> str:
    """Get a human-readable type name for a value.

    Args:
        value: Any Python value.

    Returns:
        A string describing the type (e.g., 'string', 'integer', 'array', etc.).
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


def is_numeric(value: Any) -> bool:
    """Check if a value is numeric (int or float, but not bool).

    Args:
        value: Any Python value.

    Returns:
        True if the value is numeric.
    """
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def resolve_input(file_path: Optional[str] = None) -> Tuple[Any, str]:
    """Resolve input data from a file path or stdin.

    If file_path is provided, reads from the file. Otherwise reads from stdin.

    Args:
        file_path: Optional path to a file. If None, reads from stdin.

    Returns:
        A tuple of (parsed_data, format_string).
    """
    if file_path and file_path != "-":
        data = read_file(file_path)
        fmt = detect_format(file_path)
        return data, fmt
    else:
        return read_stdin()


def output_result(data: Any, output_file: Optional[str] = None, fmt: str = "json", indent: int = 2) -> None:
    """Output data to a file or stdout.

    Args:
        data: The data to output.
        output_file: Optional file path. If None, prints to stdout.
        fmt: Output format ('json', 'yaml', 'toml', 'csv').
        indent: Indentation for JSON output.
    """
    if fmt == "json":
        content = serialize_json(data, indent=indent)
    elif fmt in ("yaml", "yml"):
        content = serialize_yaml(data)
    elif fmt == "toml":
        content = serialize_toml(data)
    elif fmt == "csv":
        content = serialize_csv(data)
    else:
        content = serialize_json(data, indent=indent)

    if output_file:
        write_file(output_file, data, fmt=fmt, indent=indent)
    else:
        print(content)
