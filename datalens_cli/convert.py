"""
Format Conversion Module for DataLens CLI.

Converts between JSON, YAML, TOML, and CSV formats.
Handles nested structures properly, with intelligent flattening for CSV.
"""

from typing import Any, Dict, List, Optional, Union

from .utils import (
    DataLensError,
    FormatNotSupportedError,
    parse_csv,
    parse_json,
    parse_toml,
    parse_yaml,
    read_file,
    serialize_csv,
    serialize_json,
    serialize_toml,
    serialize_yaml,
    write_file,
)


# Supported format names (normalized)
SUPPORTED_FORMATS = {"json", "yaml", "yml", "toml", "csv"}


def normalize_format(fmt: str) -> str:
    """Normalize a format string to a canonical form.

    Args:
        fmt: The format string to normalize.

    Returns:
        The normalized format string.

    Raises:
        FormatNotSupportedError: If the format is not supported.
    """
    fmt = fmt.lower().strip().lstrip(".")
    if fmt in ("yml", "yaml"):
        return "yaml"
    if fmt not in SUPPORTED_FORMATS:
        raise FormatNotSupportedError(
            f"不支持的格式: '{fmt}'",
            f"支持的格式: {', '.join(sorted(SUPPORTED_FORMATS))}"
        )
    return fmt


def convert(
    data: Any,
    from_format: str,
    to_format: str,
    indent: int = 2,
) -> str:
    """Convert data from one format to another.

    Args:
        data: The parsed data to convert.
        from_format: The source format.
        to_format: The target format.
        indent: Indentation for JSON output.

    Returns:
        The converted data as a string in the target format.

    Raises:
        FormatNotSupportedError: If either format is not supported.
        DataLensError: If conversion fails.
    """
    from_format = normalize_format(from_format)
    to_format = normalize_format(to_format)

    if from_format == to_format:
        # Same format - just re-serialize
        return _serialize(data, to_format, indent)

    # CSV to structured format requires special handling
    if from_format == "csv":
        data = _csv_to_structured(data)

    # Structured format to CSV requires special handling
    if to_format == "csv":
        return serialize_csv(_prepare_for_csv(data))

    return _serialize(data, to_format, indent)


def convert_file(
    input_path: str,
    output_path: Optional[str] = None,
    to_format: Optional[str] = None,
    indent: int = 2,
) -> str:
    """Convert a file from one format to another.

    Args:
        input_path: Path to the input file.
        output_path: Path to the output file. If None, returns the result as string.
        to_format: Target format. If None, inferred from output_path extension.
        indent: Indentation for JSON output.

    Returns:
        The converted data as a string.

    Raises:
        DataLensError: If conversion fails.
    """
    from .utils import detect_format

    data = read_file(input_path)
    from_format = detect_format(input_path)

    if to_format is None:
        if output_path:
            to_format = detect_format(output_path)
        else:
            raise DataLensError("必须指定输出格式 (--to) 或输出文件路径")

    to_format = normalize_format(to_format)
    result = convert(data, from_format, to_format, indent)

    if output_path:
        write_file(output_path, data, fmt=to_format, indent=indent)

    return result


def _serialize(data: Any, fmt: str, indent: int = 2) -> str:
    """Serialize data to the specified format string.

    Args:
        data: The data to serialize.
        fmt: The target format.
        indent: Indentation for JSON.

    Returns:
        The serialized string.
    """
    if fmt == "json":
        return serialize_json(data, indent=indent)
    elif fmt == "yaml":
        return serialize_yaml(data)
    elif fmt == "toml":
        return serialize_toml(data)
    elif fmt == "csv":
        return serialize_csv(_prepare_for_csv(data))
    else:
        raise FormatNotSupportedError(f"不支持的格式: {fmt}")


def _csv_to_structured(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert CSV data (list of flat dicts) to structured data.

    Attempts to unflatten dot-notation keys back into nested structures.

    Args:
        data: List of flat dictionaries from CSV parsing.

    Returns:
        List of dictionaries with nested structure restored.
    """
    result = []
    for row in data:
        result.append(_unflatten_dict(row))
    return result


def _unflatten_dict(flat: Dict[str, Any], sep: str = ".") -> Dict[str, Any]:
    """Unflatten a dictionary with dot-notation keys.

    Args:
        flat: A flat dictionary with dot-separated keys.
        sep: The separator used in keys.

    Returns:
        A nested dictionary.
    """
    result: Dict[str, Any] = {}

    for key, value in flat.items():
        parts = key.split(sep)
        current = result

        for i, part in enumerate(parts[:-1]):
            if part not in current:
                # Check if the next part looks like a list index
                next_part = parts[i + 1]
                if next_part.isdigit():
                    current[part] = []
                else:
                    current[part] = {}

            if isinstance(current[part], list):
                # Navigate into list
                idx = int(next_part)
                while len(current[part]) <= idx:
                    current[part].append({})
                current = current[part][idx]
            elif isinstance(current[part], dict):
                current = current[part]

        last_part = parts[-1]
        if isinstance(current, dict):
            current[last_part] = value
        elif isinstance(current, list) and last_part.isdigit():
            idx = int(last_part)
            while len(current) <= idx:
                current.append(None)
            current[idx] = value

    return result


def _prepare_for_csv(data: Any) -> List[Dict[str, Any]]:
    """Prepare data for CSV serialization.

    If data is a single dict, wraps it in a list. If data is a list of non-dicts,
    wraps each item in a dict with a 'value' key.

    Args:
        data: The data to prepare.

    Returns:
        A list of dictionaries suitable for CSV serialization.
    """
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        if not data:
            return []
        if all(isinstance(item, dict) for item in data):
            return data
        # Wrap non-dict items
        return [{"value": item} for item in data]
    return [{"value": data}]
