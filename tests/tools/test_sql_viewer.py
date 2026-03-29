from __future__ import annotations

import pytest
import yaml
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from tools.sql_viewer import _format_sql, _load_queries_config, _save_queries_config


class TestFormatSql:
    def test_formats_keywords_uppercase(self):
        result = _format_sql("select * from foo where x = 1")
        assert "SELECT" in result
        assert "FROM" in result
        assert "WHERE" in result

    def test_preserves_content(self):
        result = _format_sql("select col1, col2 from mytable")
        assert "col1" in result
        assert "mytable" in result


class TestQueryConfig:
    def test_save_and_load(self, tmp_path, monkeypatch):
        test_file = tmp_path / "queries.yaml"
        monkeypatch.setattr("tools.sql_viewer.QUERIES_PATH", test_file)

        data = {"dashboard_queries": [{"name": "test_q", "description": "A test", "sql": "SELECT 1"}]}
        _save_queries_config(data)

        loaded = _load_queries_config()
        assert len(loaded["dashboard_queries"]) == 1
        assert loaded["dashboard_queries"][0]["name"] == "test_q"
