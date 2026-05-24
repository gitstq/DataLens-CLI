"""DataLens CLI 核心功能单元测试"""
import json
import os
import tempfile
import pytest
from pathlib import Path
from datalens_cli.query import query
from datalens_cli.schema import infer_schema
from datalens_cli.diff import diff
from datalens_cli.merge import deep_merge
from datalens_cli.convert import convert
from datalens_cli.filter import filter_data
from datalens_cli.stats import compute_stats
from datalens_cli.validate import validate


# ============================================================
# 测试数据
# ============================================================
SAMPLE_DATA = {
    "users": [
        {"name": "Alice", "age": 30, "email": "alice@example.com", "active": True},
        {"name": "Bob", "age": 25, "email": "bob@example.com", "active": False},
        {"name": "Charlie", "age": 35, "email": "charlie@example.com", "active": True},
    ],
    "count": 3,
    "metadata": {
        "version": "1.0",
        "tags": ["alpha", "beta"]
    }
}

SAMPLE_DATA_2 = {
    "users": [
        {"name": "Alice", "age": 31, "email": "alice@example.com", "active": True},
        {"name": "Bob", "age": 25, "email": "bob@example.com", "active": False},
    ],
    "count": 2,
    "metadata": {
        "version": "2.0",
        "tags": ["alpha", "gamma"]
    }
}


# ============================================================
# query 测试
# ============================================================
class TestQuery:
    def test_simple_key(self):
        result = query(SAMPLE_DATA, "count")
        assert result == 3

    def test_nested_key(self):
        result = query(SAMPLE_DATA, "metadata.version")
        assert result == "1.0"

    def test_array_index(self):
        result = query(SAMPLE_DATA, "users[0].name")
        assert result == "Alice"

    def test_array_wildcard(self):
        result = query(SAMPLE_DATA, "users[*].name")
        assert result == ["Alice", "Bob", "Charlie"]

    def test_array_wildcard_nested(self):
        result = query(SAMPLE_DATA, "users[*].age")
        assert result == [30, 25, 35]

    def test_recursive_descent(self):
        from datalens_cli.query import query_all
        result = query_all(SAMPLE_DATA, "..version")
        assert "1.0" in result

    def test_root_access(self):
        result = query(SAMPLE_DATA, "")
        assert result == SAMPLE_DATA

    def test_nonexistent_key(self):
        result = query(SAMPLE_DATA, "nonexistent")
        assert result is None

    def test_out_of_range_index(self):
        result = query(SAMPLE_DATA, "users[99].name")
        assert result is None

    def test_filter_expression(self):
        # 先获取users数组，再用filter过滤
        users = query(SAMPLE_DATA, "users")
        from datalens_cli.filter import filter_data
        result = filter_data(users, field="age", op=">", value=28)
        names = [u["name"] for u in result]
        assert "Alice" in names
        assert "Charlie" in names
        assert "Bob" not in names


# ============================================================
# schema 推断测试
# ============================================================
class TestSchema:
    def test_basic_inference(self):
        schema = infer_schema(SAMPLE_DATA)
        assert schema["type"] == "object"
        assert "users" in schema["properties"]
        assert "count" in schema["properties"]

    def test_array_items_inference(self):
        schema = infer_schema(SAMPLE_DATA)
        users_schema = schema["properties"]["users"]
        assert users_schema["type"] == "array"
        assert users_schema["items"]["type"] == "object"

    def test_type_detection(self):
        schema = infer_schema(SAMPLE_DATA)
        assert schema["properties"]["count"]["type"] == "integer"
        assert schema["properties"]["metadata"]["type"] == "object"

    def test_email_format_detection(self):
        schema = infer_schema(SAMPLE_DATA)
        users_items = schema["properties"]["users"]["items"]
        assert users_items["properties"]["email"]["format"] == "email"

    def test_required_fields(self):
        schema = infer_schema(SAMPLE_DATA)
        users_items = schema["properties"]["users"]["items"]
        assert "name" in users_items["required"]
        assert "age" in users_items["required"]


# ============================================================
# diff 测试
# ============================================================
class TestDiff:
    def test_identical_data(self):
        result = diff(SAMPLE_DATA, SAMPLE_DATA)
        assert len(result.added) == 0
        assert len(result.removed) == 0
        assert len(result.changed) == 0

    def test_added_field(self):
        modified = {**SAMPLE_DATA, "new_field": "hello"}
        result = diff(SAMPLE_DATA, modified)
        assert len(result.added) > 0

    def test_removed_field(self):
        modified = {k: v for k, v in SAMPLE_DATA.items() if k != "count"}
        result = diff(SAMPLE_DATA, modified)
        assert len(result.removed) > 0

    def test_changed_value(self):
        result = diff(SAMPLE_DATA, SAMPLE_DATA_2)
        assert len(result.changed) > 0


# ============================================================
# merge 测试
# ============================================================
class TestMerge:
    def test_simple_merge(self):
        a = {"x": 1, "y": 2}
        b = {"y": 3, "z": 4}
        result = deep_merge(a, b)
        assert result["x"] == 1
        assert result["y"] == 3
        assert result["z"] == 4

    def test_deep_merge(self):
        a = {"a": {"b": 1, "c": 2}}
        b = {"a": {"c": 3, "d": 4}}
        result = deep_merge(a, b)
        assert result["a"]["b"] == 1
        assert result["a"]["c"] == 3
        assert result["a"]["d"] == 4

    def test_empty_merge(self):
        result = deep_merge({}, {"a": 1})
        assert result == {"a": 1}


# ============================================================
# convert 测试
# ============================================================
class TestConvert:
    def test_json_to_json(self):
        result = convert(SAMPLE_DATA, "json", "json")
        assert json.loads(result) == SAMPLE_DATA

    def test_json_to_csv(self):
        result = convert(SAMPLE_DATA, "json", "csv")
        assert "users" in result or "name" in result

    def test_invalid_format(self):
        with pytest.raises(Exception):
            convert(SAMPLE_DATA, "json", "invalid_format")


# ============================================================
# filter 测试
# ============================================================
class TestFilter:
    def test_filter_equals(self):
        users = SAMPLE_DATA["users"]
        result = filter_data(users, field="name", op="==", value="Alice")
        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    def test_filter_greater_than(self):
        users = SAMPLE_DATA["users"]
        result = filter_data(users, field="age", op=">", value=28)
        assert len(result) == 2

    def test_filter_contains(self):
        users = SAMPLE_DATA["users"]
        result = filter_data(users, field="email", op="contains", value="alice")
        assert len(result) == 1

    def test_no_match(self):
        users = SAMPLE_DATA["users"]
        result = filter_data(users, field="name", op="==", value="NonExistent")
        assert len(result) == 0


# ============================================================
# stats 测试
# ============================================================
class TestStats:
    def test_basic_stats(self):
        stats = compute_stats(SAMPLE_DATA)
        assert stats is not None

    def test_object_stats(self):
        stats = compute_stats(SAMPLE_DATA)
        assert stats is not None

    def test_array_stats(self):
        stats = compute_stats([1, 2, 3, 4, 5])
        assert stats is not None


# ============================================================
# validate 测试
# ============================================================
class TestValidate:
    def test_valid_against_inferred_schema(self):
        schema = infer_schema(SAMPLE_DATA)
        result = validate(SAMPLE_DATA, schema)
        assert result.valid is True

    def test_invalid_data(self):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"]
        }
        result = validate({"age": 25}, schema)
        assert result.valid is False

    def test_type_mismatch(self):
        schema = {
            "type": "object",
            "properties": {"age": {"type": "integer"}},
            "required": ["age"]
        }
        result = validate({"age": "not_a_number"}, schema)
        assert result.valid is False


# ============================================================
# 集成测试 - 文件读写
# ============================================================
class TestFileIntegration:
    def test_query_from_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(SAMPLE_DATA, f)
            f.flush()
            from datalens_cli.utils import read_file
            data = read_file(Path(f.name))
            assert data == SAMPLE_DATA
            os.unlink(f.name)

    def test_empty_file_handling(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{}")
            f.flush()
            from datalens_cli.utils import read_file
            data = read_file(Path(f.name))
            assert data == {}
            os.unlink(f.name)
