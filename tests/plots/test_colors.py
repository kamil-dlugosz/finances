from __future__ import annotations

import pandas as pd
import pytest

from plots.colors import (
    TIER1_PALETTE,
    DIM_COLOR,
    tier1_color_map,
    color_for_depth,
    tx_color,
    compact_fmt,
    compact_fmt_js,
)


class TestTier1ColorMap:
    def test_returns_dict(self):
        df = pd.DataFrame({"Tier1": ["A", "B", "A", "C"]})
        result = tier1_color_map(df)
        assert isinstance(result, dict)
        assert set(result.keys()) == {"A", "B", "C"}

    def test_deterministic(self):
        df = pd.DataFrame({"Tier1": ["B", "A", "C"]})
        r1 = tier1_color_map(df)
        r2 = tier1_color_map(df)
        assert r1 == r2

    def test_uses_palette(self):
        df = pd.DataFrame({"Tier1": ["X"]})
        result = tier1_color_map(df)
        assert result["X"] == TIER1_PALETTE[0]


class TestColorForDepth:
    def test_depth_1_unchanged(self):
        base = "hsl(210,60%,50%)"
        result = color_for_depth(base, 1)
        assert "50%" in result

    def test_depth_increases_lightness(self):
        base = "hsl(210,60%,50%)"
        result = color_for_depth(base, 3)
        assert "66%" in result

    def test_handles_whitespace_in_hsl(self):
        result = color_for_depth("hsl(210, 60%, 50%)", 2)
        assert "58%" in result


class TestTxColor:
    def test_adds_opacity(self):
        result = tx_color("hsl(210,60%,50%)")
        assert "hsla(" in result
        assert "0.45" in result


class TestCompactFmt:
    def test_zero(self):
        assert compact_fmt(0) == "0"

    def test_thousands(self):
        assert compact_fmt(23281) == "23k"

    def test_thousands_with_remainder(self):
        assert compact_fmt(7903) == "7k 900"

    def test_hundreds(self):
        assert compact_fmt(982) == "980"

    def test_small(self):
        assert compact_fmt(156) == "160"

    def test_negative(self):
        assert compact_fmt(-23281) == "-23k"

    def test_very_small(self):
        assert compact_fmt(45) == "45"


class TestCompactFmtJs:
    def test_returns_js_function(self):
        js = compact_fmt_js()
        assert "function compactFmt" in js
        assert "return" in js
