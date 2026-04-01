from __future__ import annotations

import math

import pandas as pd

from config import get_tier_tree

TIER1_PALETTE = [
    "hsl(210,60%,50%)",
    "hsl(30,70%,50%)",
    "hsl(130,50%,45%)",
    "hsl(0,60%,50%)",
    "hsl(270,50%,55%)",
    "hsl(50,70%,48%)",
    "hsl(180,50%,45%)",
    "hsl(330,55%,50%)",
]

DIM_COLOR = "hsl(0,0%,78%)"
TX_OPACITY = 0.45


def tier1_color_map(df: pd.DataFrame) -> dict[str, str]:
    """Return a deterministic mapping of Tier1 values to palette colours in config order."""
    present = set(df["Tier1"].dropna().unique())
    tier1_vals = [v for v in get_tier_tree().tier_order(1) if v in present]
    for v in sorted(present - set(tier1_vals)):
        tier1_vals.append(v)
    return {v: TIER1_PALETTE[i % len(TIER1_PALETTE)] for i, v in enumerate(tier1_vals)}


def color_for_depth(base_hsl: str, tier_depth: int) -> str:
    """Lighten *base_hsl* by ``(tier_depth-1)*8`` lightness-percent points."""
    parts = [p.strip() for p in base_hsl.split(",")]
    if len(parts) != 3:
        return base_hsl
    h, s, l_part = parts
    l_val = int(l_part.replace("%)", "").strip())
    return f"{h},{s},{min(l_val + (tier_depth - 1) * 8, 85)}%)"


def tx_color(base_hsl: str) -> str:
    """Semi-transparent version of *base_hsl* for individual transactions."""
    return base_hsl.replace(")", f",{TX_OPACITY})").replace("hsl(", "hsla(")


def compact_fmt(val: float) -> str:
    """Round *val* to 2 significant figures and format with ``k`` suffix.

    Examples::

        23281 -> "23k"
        7903  -> "7k 900"
        982   -> "980"
        156   -> "160"
        45    -> "45"
    """
    if val == 0:
        return "0"

    negative = val < 0
    v = abs(val)

    if v < 1:
        return f"-{v:.2f}" if negative else f"{v:.2f}"

    digits = int(math.floor(math.log10(v))) + 1
    if digits <= 2:
        rounded = round(v, -(digits - 2)) if digits > 1 else round(v)
        result = str(int(rounded))
    else:
        rounded = round(v, -(digits - 2))
        rounded_int = int(rounded)
        if rounded_int >= 1000:
            thousands = rounded_int // 1000
            remainder = rounded_int % 1000
            if remainder == 0:
                result = f"{thousands}k"
            else:
                result = f"{thousands}k {remainder}"
        else:
            result = str(rounded_int)

    return f"-{result}" if negative else result


def compact_fmt_js() -> str:
    """Return a JS function body equivalent to :func:`compact_fmt`."""
    return r"""
function compactFmt(val) {
  if (val === 0) return '0';
  var neg = val < 0;
  var v = Math.abs(val);
  if (v < 1) return (neg ? '-' : '') + v.toFixed(2);
  var digits = Math.floor(Math.log10(v)) + 1;
  var rounded;
  if (digits <= 2) {
    var p = Math.pow(10, digits - 2);
    rounded = Math.round(v / p) * p;
    return (neg ? '-' : '') + String(Math.round(rounded));
  }
  var p2 = Math.pow(10, digits - 2);
  rounded = Math.round(v / p2) * p2;
  var ri = Math.round(rounded);
  if (ri >= 1000) {
    var th = Math.floor(ri / 1000);
    var rem = ri % 1000;
    return (neg ? '-' : '') + (rem === 0 ? th + 'k' : th + 'k ' + rem);
  }
  return (neg ? '-' : '') + String(ri);
}
""".strip()
