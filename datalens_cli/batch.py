"""
Batch Processing Module for DataLens CLI.

Processes multiple files at once, applying a single command to each file.
Supports parallel processing, output collection, and error aggregation.
"""

import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .utils import (
    DataLensError,
    Colors,
    safe_colorize,
    read_file,
    serialize_json,
)


class BatchResult:
    """Result of a batch processing operation.

    Attributes:
        total: Total number of files processed.
        succeeded: Number of files processed successfully.
        failed: Number of files that failed.
        results: List of (file_path, result) tuples for successful operations.
        errors: List of (file_path, error_message) tuples for failed operations.
    """

    def __init__(self):
        self.total: int = 0
        self.succeeded: int = 0
        self.failed: int = 0
        self.results: List[Tuple[str, Any]] = []
        self.errors: List[Tuple[str, str]] = []

    def add_success(self, file_path: str, result: Any) -> None:
        """Record a successful file processing.

        Args:
            file_path: The file that was processed.
            result: The processing result.
        """
        self.total += 1
        self.succeeded += 1
        self.results.append((file_path, result))

    def add_failure(self, file_path: str, error: str) -> None:
        """Record a failed file processing.

        Args:
            file_path: The file that failed.
            error: The error message.
        """
        self.total += 1
        self.failed += 1
        self.errors.append((file_path, error))

    def summary(self, use_color: bool = True) -> str:
        """Generate a summary of the batch operation.

        Args:
            use_color: Whether to use ANSI color codes.

        Returns:
            A formatted summary string.
        """
        lines: List[str] = []

        title = safe_colorize("批量处理结果", Colors.BOLD + Colors.CYAN) if use_color \
            else "批量处理结果"
        lines.append(title)
        lines.append("=" * 50)

        total_str = f"总计: {self.total}"
        lines.append(total_str)

        if self.succeeded > 0:
            success_str = safe_colorize(
                f"成功: {self.succeeded}", Colors.GREEN
            ) if use_color else f"成功: {self.succeeded}"
            lines.append(success_str)

        if self.failed > 0:
            fail_str = safe_colorize(
                f"失败: {self.failed}", Colors.RED
            ) if use_color else f"失败: {self.failed}"
            lines.append(fail_str)

        if self.errors:
            lines.append("")
            error_header = safe_colorize("错误详情:", Colors.RED) if use_color \
                else "错误详情:"
            lines.append(error_header)
            for file_path, error in self.errors:
                if use_color:
                    lines.append(f"  {safe_colorize(file_path, Colors.YELLOW)}: {error}")
                else:
                    lines.append(f"  {file_path}: {error}")

        return "\n".join(lines)


# Type alias for batch operation functions
BatchOperation = Callable[[str, Any], Any]


def batch_process(
    file_paths: List[str],
    operation: str,
    operation_args: Optional[Dict[str, Any]] = None,
    output_dir: Optional[str] = None,
    output_format: Optional[str] = None,
) -> BatchResult:
    """Process multiple files with a specified operation.

    Args:
        file_paths: List of file paths to process.
        operation: The operation to perform (query, convert, validate, stats, etc.).
        operation_args: Additional arguments for the operation.
        output_dir: Optional directory to write output files.
        output_format: Optional output format for converted files.

    Returns:
        A BatchResult with the outcomes of all operations.
    """
    result = BatchResult()
    operation_args = operation_args or {}

    for file_path in file_paths:
        try:
            path = Path(file_path)
            if not path.exists():
                result.add_failure(file_path, "文件不存在")
                continue

            data = read_file(file_path)
            op_result = _execute_operation(operation, data, file_path, operation_args)

            result.add_success(file_path, op_result)

            # Write output if requested
            if output_dir:
                _write_batch_output(
                    file_path, op_result, output_dir, output_format, operation
                )

        except Exception as e:
            result.add_failure(file_path, str(e))

    return result


def _execute_operation(
    operation: str,
    data: Any,
    file_path: str,
    args: Dict[str, Any],
) -> Any:
    """Execute a specific operation on data.

    Args:
        operation: The operation name.
        data: The parsed data.
        file_path: The source file path.
        args: Operation arguments.

    Returns:
        The operation result.

    Raises:
        DataLensError: If the operation is not supported.
    """
    if operation == "query":
        from .query import query
        expression = args.get("expression", "")
        if not expression:
            raise DataLensError("查询操作需要 --expr 参数")
        return query(data, expression)

    elif operation == "convert":
        from .convert import convert, normalize_format
        from .utils import detect_format
        to_format = args.get("to_format", "json")
        to_format = normalize_format(to_format)
        from_format = detect_format(file_path)
        return convert(data, from_format, to_format)

    elif operation == "validate":
        from .validate import validate
        schema = args.get("schema")
        if schema is None:
            raise DataLensError("验证操作需要 --schema 参数")
        if isinstance(schema, str):
            import json as json_module
            from pathlib import Path as _Path
            schema = json_module.loads(_Path(schema).read_text(encoding="utf-8"))
        result = validate(data, schema)
        return {"valid": result.valid, "errors": result.errors}

    elif operation == "schema":
        from .schema import infer_schema
        return infer_schema(data)

    elif operation == "stats":
        from .stats import compute_stats
        stats = compute_stats(data)
        return stats.summary()

    elif operation == "pretty":
        from .format import pretty_print
        indent = args.get("indent", 2)
        fmt = args.get("format", "json")
        return pretty_print(data, indent=indent, color=False, format_type=fmt)

    elif operation == "filter":
        from .filter import filter_data
        field = args.get("field")
        op = args.get("op", "==")
        value = args.get("value")
        if not field:
            raise DataLensError("过滤操作需要 --field 参数")
        if not isinstance(data, list):
            raise DataLensError("过滤操作要求数据为列表")
        return filter_data(data, field=field, op=op, value=value)

    elif operation == "sort":
        from .filter import sort_data
        field = args.get("field")
        reverse = args.get("reverse", False)
        if not field:
            raise DataLensError("排序操作需要 --field 参数")
        if not isinstance(data, list):
            raise DataLensError("排序操作要求数据为列表")
        return sort_data(data, field=field, reverse=reverse)

    else:
        raise DataLensError(f"不支持的批量操作: '{operation}'")


def _write_batch_output(
    input_path: str,
    result: Any,
    output_dir: str,
    output_format: Optional[str],
    operation: str,
) -> None:
    """Write the result of a batch operation to an output file.

    Args:
        input_path: The input file path.
        result: The operation result.
        output_dir: The output directory.
        output_format: The output format.
        operation: The operation name.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    input_name = Path(input_path).stem

    if output_format:
        ext = f".{output_format.lstrip('.')}"
    else:
        ext = Path(input_path).suffix

    output_path = out / f"{input_name}_{operation}{ext}"

    if isinstance(result, str):
        output_path.write_text(result, encoding="utf-8")
    else:
        output_path.write_text(
            serialize_json(result, indent=2), encoding="utf-8"
        )


def batch_query(
    file_paths: List[str],
    expression: str,
    output_dir: Optional[str] = None,
) -> BatchResult:
    """Batch query multiple files with the same expression.

    Args:
        file_paths: List of file paths.
        expression: The query expression.
        output_dir: Optional output directory.

    Returns:
        A BatchResult.
    """
    return batch_process(
        file_paths,
        "query",
        operation_args={"expression": expression},
        output_dir=output_dir,
    )


def batch_convert(
    file_paths: List[str],
    to_format: str,
    output_dir: Optional[str] = None,
) -> BatchResult:
    """Batch convert multiple files to a target format.

    Args:
        file_paths: List of file paths.
        to_format: Target format.
        output_dir: Optional output directory.

    Returns:
        A BatchResult.
    """
    return batch_process(
        file_paths,
        "convert",
        operation_args={"to_format": to_format},
        output_dir=output_dir,
        output_format=to_format,
    )


def batch_validate(
    file_paths: List[str],
    schema: Any,
) -> BatchResult:
    """Batch validate multiple files against a schema.

    Args:
        file_paths: List of file paths.
        schema: The JSON Schema (dict or path to schema file).

    Returns:
        A BatchResult.
    """
    return batch_process(
        file_paths,
        "validate",
        operation_args={"schema": schema},
    )
