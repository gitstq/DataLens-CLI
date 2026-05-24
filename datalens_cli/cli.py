"""
DataLens CLI - Main Command-Line Interface.

Provides the `datalens` command with subcommands for querying, converting,
validating, comparing, and processing structured data files.

Usage:
    datalens query <file> <expression>
    datalens convert <file> --to <format>
    datalens validate <file> --schema <schema_file>
    datalens schema <file>
    datalens diff <file1> <file2>
    datalens pretty <file> [--indent N]
    datalens merge <file1> <file2> ...
    datalens filter <file> --field <f> --op <op> --value <v>
    datalens stats <file>
    datalens batch <command> <files...>
"""

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from . import __version__


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for the DataLens CLI.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"datalens-cli {__version__}")
        return 0

    if not args.command:
        parser.print_help()
        return 0

    try:
        return _dispatch_command(args)
    except KeyboardInterrupt:
        print("\n操作已取消", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with all subcommands.

    Returns:
        The configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog="datalens",
        description="DataLens CLI - 轻量级终端 JSON/YAML/TOML 智能数据处理引擎",
        epilog="示例:\n"
               "  datalens query data.json 'users[0].name'\n"
               "  datalens convert data.yaml --to json\n"
               "  datalens diff old.json new.json\n"
               "  datalens stats data.json\n"
               "  cat data.json | datalens query '.users[*].name'\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-v", "--version", action="store_true", help="显示版本号")

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # --- query ---
    query_parser = subparsers.add_parser(
        "query", help="使用点表示法或 JSONPath 查询数据"
    )
    query_parser.add_argument("file", nargs="?", help="数据文件路径 (留空则从 stdin 读取)")
    query_parser.add_argument("expression", help="查询表达式 (例如: 'users[0].name')")
    query_parser.add_argument("-o", "--output", help="输出文件路径")
    query_parser.add_argument("--raw", action="store_true", help="原始输出 (无格式化)")
    query_parser.add_argument("--indent", type=int, default=2, help="缩进空格数 (默认: 2)")

    # --- convert ---
    convert_parser = subparsers.add_parser(
        "convert", help="转换数据格式 (JSON/YAML/TOML/CSV)"
    )
    convert_parser.add_argument("file", help="输入文件路径")
    convert_parser.add_argument("-t", "--to", dest="to_format", required=True,
                               help="目标格式 (json/yaml/toml/csv)")
    convert_parser.add_argument("-o", "--output", help="输出文件路径")
    convert_parser.add_argument("--indent", type=int, default=2, help="缩进空格数 (默认: 2)")

    # --- validate ---
    validate_parser = subparsers.add_parser(
        "validate", help="根据 JSON Schema 验证数据"
    )
    validate_parser.add_argument("file", help="数据文件路径")
    validate_parser.add_argument("-s", "--schema", required=True, help="Schema 文件路径")
    validate_parser.add_argument("--quiet", action="store_true", help="仅输出错误")

    # --- schema ---
    schema_parser = subparsers.add_parser(
        "schema", help="从样本数据推断 JSON Schema"
    )
    schema_parser.add_argument("file", help="数据文件路径")
    schema_parser.add_argument("-o", "--output", help="输出文件路径")
    schema_parser.add_argument("--title", help="Schema 标题")
    schema_parser.add_argument("--indent", type=int, default=2, help="缩进空格数 (默认: 2)")

    # --- diff ---
    diff_parser = subparsers.add_parser(
        "diff", help="深度比较两个数据文件"
    )
    diff_parser.add_argument("file1", help="第一个文件路径")
    diff_parser.add_argument("file2", help="第二个文件路径")
    diff_parser.add_argument("--no-color", action="store_true", help="禁用颜色输出")

    # --- pretty ---
    pretty_parser = subparsers.add_parser(
        "pretty", help="语法高亮美化打印数据"
    )
    pretty_parser.add_argument("file", nargs="?", help="数据文件路径 (留空则从 stdin 读取)")
    pretty_parser.add_argument("--indent", type=int, default=2, help="缩进空格数 (默认: 2)")
    pretty_parser.add_argument("--format", dest="fmt", default="json",
                               help="输出格式 (json/yaml/toml/csv, 默认: json)")
    pretty_parser.add_argument("--no-color", action="store_true", help="禁用颜色输出")

    # --- merge ---
    merge_parser = subparsers.add_parser(
        "merge", help="深度合并多个数据文件"
    )
    merge_parser.add_argument("files", nargs="+", help="要合并的文件路径")
    merge_parser.add_argument("-o", "--output", help="输出文件路径")
    merge_parser.add_argument("--strategy", default="overwrite",
                              choices=["overwrite", "append", "prepend", "unique", "deep"],
                              help="合并策略 (默认: overwrite)")
    merge_parser.add_argument("--indent", type=int, default=2, help="缩进空格数 (默认: 2)")

    # --- filter ---
    filter_parser = subparsers.add_parser(
        "filter", help="过滤和排序数据"
    )
    filter_parser.add_argument("file", nargs="?", help="数据文件路径 (留空则从 stdin 读取)")
    filter_parser.add_argument("-f", "--field", help="过滤字段名")
    filter_parser.add_argument("--op", default="==",
                               help="比较运算符 (==, !=, >, <, >=, <=, contains, regex, in, exists)")
    filter_parser.add_argument("--value", help="比较值")
    filter_parser.add_argument("--sort", dest="sort_field", help="排序字段")
    filter_parser.add_argument("--desc", action="store_true", help="降序排序")
    filter_parser.add_argument("--limit", type=int, help="限制结果数量")
    filter_parser.add_argument("--offset", type=int, default=0, help="跳过前 N 条")
    filter_parser.add_argument("--select", help="选择特定字段 (逗号分隔)")
    filter_parser.add_argument("-o", "--output", help="输出文件路径")
    filter_parser.add_argument("--indent", type=int, default=2, help="缩进空格数 (默认: 2)")

    # --- stats ---
    stats_parser = subparsers.add_parser(
        "stats", help="显示数据结构统计信息"
    )
    stats_parser.add_argument("file", help="数据文件路径")
    stats_parser.add_argument("--no-color", action="store_true", help="禁用颜色输出")

    # --- batch ---
    batch_parser = subparsers.add_parser(
        "batch", help="批量处理多个文件"
    )
    batch_parser.add_argument("subcommand", help="要执行的命令 (query/convert/validate/stats)")
    batch_parser.add_argument("files", nargs="+", help="文件路径列表")
    batch_parser.add_argument("--expr", help="查询表达式 (用于 query 命令)")
    batch_parser.add_argument("--to", dest="to_format", help="目标格式 (用于 convert 命令)")
    batch_parser.add_argument("--schema", help="Schema 文件 (用于 validate 命令)")
    batch_parser.add_argument("--output-dir", help="输出目录")
    batch_parser.add_argument("--field", help="过滤字段 (用于 filter 命令)")
    batch_parser.add_argument("--op", default="==", help="过滤运算符")
    batch_parser.add_argument("--value", help="过滤值")

    return parser


def _dispatch_command(args: argparse.Namespace) -> int:
    """Dispatch to the appropriate command handler.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    command = args.command

    if command == "query":
        return _cmd_query(args)
    elif command == "convert":
        return _cmd_convert(args)
    elif command == "validate":
        return _cmd_validate(args)
    elif command == "schema":
        return _cmd_schema(args)
    elif command == "diff":
        return _cmd_diff(args)
    elif command == "pretty":
        return _cmd_pretty(args)
    elif command == "merge":
        return _cmd_merge(args)
    elif command == "filter":
        return _cmd_filter(args)
    elif command == "stats":
        return _cmd_stats(args)
    elif command == "batch":
        return _cmd_batch(args)
    else:
        print(f"未知命令: {command}", file=sys.stderr)
        return 1


# ---------------------------------------------------------------------------
# Command Handlers
# ---------------------------------------------------------------------------

def _cmd_query(args: argparse.Namespace) -> int:
    """Handle the 'query' command.

    Args:
        args: Parsed arguments.

    Returns:
        Exit code.
    """
    from .query import query, QueryError
    from .utils import resolve_input, output_result

    data, fmt = resolve_input(args.file)
    expression = args.expression

    try:
        result = query(data, expression)
    except QueryError as e:
        print(f"查询错误: {e}", file=sys.stderr)
        return 1

    if result is None:
        print("(无匹配结果)", file=sys.stderr)
        return 1

    if args.raw:
        if isinstance(result, (dict, list)):
            print(json.dumps(result, ensure_ascii=False, default=str))
        else:
            print(result)
    else:
        output_result(result, args.output, indent=args.indent)

    return 0


def _cmd_convert(args: argparse.Namespace) -> int:
    """Handle the 'convert' command.

    Args:
        args: Parsed arguments.

    Returns:
        Exit code.
    """
    from .convert import convert_file

    try:
        result = convert_file(
            args.file,
            output_path=args.output,
            to_format=args.to_format,
            indent=args.indent,
        )
        if not args.output:
            print(result)
    except Exception as e:
        print(f"转换失败: {e}", file=sys.stderr)
        return 1

    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    """Handle the 'validate' command.

    Args:
        args: Parsed arguments.

    Returns:
        Exit code.
    """
    from .validate import validate_file
    from .utils import Colors, safe_colorize

    try:
        result = validate_file(args.file, args.schema)
    except Exception as e:
        print(f"验证失败: {e}", file=sys.stderr)
        return 1

    if result.valid:
        if not args.quiet:
            msg = safe_colorize("验证通过 - 数据符合 Schema", Colors.GREEN)
            print(msg)
        return 0
    else:
        msg = safe_colorize(f"验证失败 - 发现 {len(result.errors)} 个错误", Colors.RED)
        print(msg)
        for error in result.errors:
            print(f"  - {error}")
        return 1


def _cmd_schema(args: argparse.Namespace) -> int:
    """Handle the 'schema' command.

    Args:
        args: Parsed arguments.

    Returns:
        Exit code.
    """
    from .schema import infer_schema_from_file
    from .utils import output_result

    try:
        schema = infer_schema_from_file(args.file, title=args.title)
    except Exception as e:
        print(f"Schema 推断失败: {e}", file=sys.stderr)
        return 1

    output_result(schema, args.output, indent=args.indent)
    return 0


def _cmd_diff(args: argparse.Namespace) -> int:
    """Handle the 'diff' command.

    Args:
        args: Parsed arguments.

    Returns:
        Exit code.
    """
    from .diff import diff_files, format_diff

    try:
        result = diff_files(args.file1, args.file2)
    except Exception as e:
        print(f"比较失败: {e}", file=sys.stderr)
        return 1

    use_color = not args.no_color
    print(format_diff(result, use_color=use_color))

    return 0 if result.is_identical else 2


def _cmd_pretty(args: argparse.Namespace) -> int:
    """Handle the 'pretty' command.

    Args:
        args: Parsed arguments.

    Returns:
        Exit code.
    """
    from .format import print_data
    from .utils import resolve_input

    data, fmt = resolve_input(args.file)
    use_color = not args.no_color

    print_data(data, indent=args.indent, color=use_color, format_type=args.fmt)
    return 0


def _cmd_merge(args: argparse.Namespace) -> int:
    """Handle the 'merge' command.

    Args:
        args: Parsed arguments.

    Returns:
        Exit code.
    """
    from .merge import merge_files
    from .utils import output_result

    try:
        result = merge_files(args.files, strategy=args.strategy)
    except Exception as e:
        print(f"合并失败: {e}", file=sys.stderr)
        return 1

    output_result(result, args.output, indent=args.indent)
    return 0


def _cmd_filter(args: argparse.Namespace) -> int:
    """Handle the 'filter' command.

    Args:
        args: Parsed arguments.

    Returns:
        Exit code.
    """
    from .filter import filter_data, sort_data, limit as limit_fn, select_fields, FilterError
    from .utils import resolve_input, output_result, parse_json

    data, fmt = resolve_input(args.file)

    if not isinstance(data, list):
        print("错误: 过滤操作要求数据为列表 (array)", file=sys.stderr)
        return 1

    # Apply filter
    if args.field:
        # Parse the value
        value = args.value
        if value is not None:
            try:
                value = parse_json(value)
            except Exception:
                # Keep as string
                pass

        try:
            data = filter_data(data, field=args.field, op=args.op, value=value)
        except FilterError as e:
            print(f"过滤错误: {e}", file=sys.stderr)
            return 1

    # Apply sort
    if args.sort_field:
        data = sort_data(data, field=args.sort_field, reverse=args.desc)

    # Apply offset and limit
    if args.offset > 0 or args.limit:
        lim = args.limit if args.limit else len(data)
        data = limit_fn(data, lim, args.offset)

    # Apply field selection
    if args.select:
        fields = [f.strip() for f in args.select.split(",")]
        data = select_fields(data, fields)

    output_result(data, args.output, indent=args.indent)
    return 0


def _cmd_stats(args: argparse.Namespace) -> int:
    """Handle the 'stats' command.

    Args:
        args: Parsed arguments.

    Returns:
        Exit code.
    """
    from .stats import compute_stats_file

    try:
        stats = compute_stats_file(args.file)
    except Exception as e:
        print(f"统计失败: {e}", file=sys.stderr)
        return 1

    use_color = not args.no_color
    print(stats.summary(use_color=use_color))
    return 0


def _cmd_batch(args: argparse.Namespace) -> int:
    """Handle the 'batch' command.

    Args:
        args: Parsed arguments.

    Returns:
        Exit code.
    """
    from .batch import batch_process
    from .utils import Colors, safe_colorize

    operation_args: Dict[str, Any] = {}

    if args.expr:
        operation_args["expression"] = args.expr
    if args.to_format:
        operation_args["to_format"] = args.to_format
    if args.schema:
        operation_args["schema"] = args.schema
    if args.field:
        operation_args["field"] = args.field
        operation_args["op"] = args.op
        operation_args["value"] = args.value

    result = batch_process(
        args.files,
        args.subcommand,
        operation_args=operation_args,
        output_dir=args.output_dir,
    )

    print(result.summary())

    return 0 if result.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
