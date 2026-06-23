#!/usr/bin/env python3
"""ta-engine / ta: technical-analysis indicator engine over any OHLCV array.

Asset-agnostic. Feed klines pulled from any of:
  - crypto-markets/scripts/spot.py klines   (Binance)
  - global-markets/scripts/equity.py history (Eastmoney/Yahoo/Nasdaq)
  - cn-markets/scripts/equity.py history     (Eastmoney/Sina/Tencent)
  - cn-markets/scripts/futures.py / global-markets/scripts/futures.py

The script accepts JSON from a file (`--input`) or stdin (`-`) and
auto-detects the shape. See `references/input-shapes.md`.

Uses pandas-ta (lazy-imported — install at skill root: `uv sync
--frozen`, then invoke via `uv run scripts/ta.py …`).

Output: JSON to stdout. Errors: JSON {"error": "..."} with exit code 1.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, NoReturn


def die(msg: str, *, install: str | None = None, code: int = 1) -> NoReturn:
    payload: dict[str, Any] = {"error": msg}
    if install:
        payload["install"] = install
    print(json.dumps(payload, ensure_ascii=False))
    sys.exit(code)


def _deps():
    """Lazy import pandas + pandas-ta."""
    try:
        import pandas as pd
        import pandas_ta as pta  # type: ignore
    except ImportError as e:
        die(f"missing dep: {e.name}", install="uv sync --frozen   # at skill root, then re-invoke via `uv run scripts/ta.py …`", code=2)
    return pd, pta


# ---------- Input parsing ----------

_OHLC_KEYS = {
    "open":   ["open", "o", "Open", "openPrice"],
    "high":   ["high", "h", "High", "highPrice"],
    "low":    ["low", "l", "Low", "lowPrice"],
    "close":  ["close", "c", "Close", "closePrice", "price"],
    "volume": ["volume", "v", "Volume", "vol"],
}
_TS_KEYS = ["open_time", "close_time", "timestamp", "ts", "time", "date", "datetime", "Date", "day"]


def _pick(d: dict, keys: list[str]):
    for k in keys:
        if k in d:
            return d[k]
    return None


def _load_input(path: str) -> list[dict[str, Any]]:
    """Read JSON from path ('-' = stdin) and normalize to a list of dicts with
    open/high/low/close/volume/timestamp keys."""
    raw_text = sys.stdin.read() if path == "-" else open(path).read()
    j = json.loads(raw_text)

    # Walk into common container shapes.
    if isinstance(j, dict):
        for container in ("klines", "history", "series", "rows", "data", "ohlcv"):
            if container in j and isinstance(j[container], list):
                j = j[container]
                break

    if not isinstance(j, list) or not j:
        die("input is not a non-empty list of OHLCV rows (after walking container keys)")

    rows: list[dict[str, Any]] = []
    sample = j[0]
    if isinstance(sample, list):
        # Binance raw kline format: [open_time, open, high, low, close, volume, close_time, ...]
        for r in j:
            rows.append({
                "timestamp": r[0],
                "open": float(r[1]),
                "high": float(r[2]),
                "low": float(r[3]),
                "close": float(r[4]),
                "volume": float(r[5]),
            })
    elif isinstance(sample, dict):
        for r in j:
            ts = _pick(r, _TS_KEYS)
            o = _pick(r, _OHLC_KEYS["open"])
            h = _pick(r, _OHLC_KEYS["high"])
            l = _pick(r, _OHLC_KEYS["low"])
            c = _pick(r, _OHLC_KEYS["close"])
            v = _pick(r, _OHLC_KEYS["volume"])
            if c is None:
                continue
            rows.append({
                "timestamp": ts,
                "open": float(o) if o is not None else float(c),
                "high": float(h) if h is not None else float(c),
                "low": float(l) if l is not None else float(c),
                "close": float(c),
                "volume": float(v) if v is not None else 0.0,
            })
    else:
        die(f"unsupported row type: {type(sample).__name__}")

    if not rows:
        die("no parseable OHLCV rows after normalization")
    return rows


def _to_df(rows: list[dict[str, Any]]):
    pd, _ = _deps()
    df = pd.DataFrame(rows)
    # Ensure ascending order — many indicators assume time-ordered input.
    if "timestamp" in df.columns and df["timestamp"].notna().any():
        # Heuristic: epoch ms vs sec vs string date. numpy.number covers np.int64/float64.
        import numpy as np
        first = df["timestamp"].dropna().iloc[0]
        if isinstance(first, (int, float, np.integer, np.floating)):
            unit = "ms" if float(first) > 1e12 else "s"
            df["dt"] = pd.to_datetime(df["timestamp"], unit=unit, utc=True)
        else:
            df["dt"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        df = df.sort_values("dt").reset_index(drop=True)
    return df


# ---------- Indicator parsing ----------

def _parse_spec(spec: str) -> tuple[str, list[float]]:
    """'ema:20' -> ('ema', [20]); 'bbands:20:2' -> ('bbands', [20, 2])."""
    parts = spec.split(":")
    name = parts[0].lower()
    args = [float(x) if "." in x else int(x) for x in parts[1:]]
    return name, args


def _apply(df, spec: str) -> dict[str, list]:
    """Compute one indicator on df, return columnname → list[float|None]."""
    pd, pta = _deps()
    name, params = _parse_spec(spec)
    c = df["close"]
    h, l, v = df["high"], df["low"], df["volume"]

    def _ser(res, label: str | None = None):
        if res is None:
            return {label or name: [None] * len(df)}
        if isinstance(res, pd.DataFrame):
            return {col: _series_to_list(res[col]) for col in res.columns}
        if hasattr(res, "name") and res.name and not label:
            return {res.name: _series_to_list(res)}
        return {label or name: _series_to_list(res)}

    if name == "ema":
        n = int(params[0]) if params else 20
        return _ser(pta.ema(c, length=n), f"ema_{n}")
    if name == "sma":
        n = int(params[0]) if params else 20
        return _ser(pta.sma(c, length=n), f"sma_{n}")
    if name == "wma":
        n = int(params[0]) if params else 20
        return _ser(pta.wma(c, length=n), f"wma_{n}")
    if name == "rsi":
        n = int(params[0]) if params else 14
        return _ser(pta.rsi(c, length=n), f"rsi_{n}")
    if name == "macd":
        fast, slow, sig = (params + [12, 26, 9])[:3]
        df_macd = pta.macd(c, fast=int(fast), slow=int(slow), signal=int(sig))
        return _ser(df_macd) if df_macd is not None else {}
    if name == "bbands":
        n = int(params[0]) if params else 20
        sd = float(params[1]) if len(params) > 1 else 2.0
        df_bb = pta.bbands(c, length=n, std=sd)
        return _ser(df_bb) if df_bb is not None else {}
    if name == "atr":
        n = int(params[0]) if params else 14
        return _ser(pta.atr(h, l, c, length=n), f"atr_{n}")
    if name == "adx":
        n = int(params[0]) if params else 14
        df_adx = pta.adx(h, l, c, length=n)
        return _ser(df_adx) if df_adx is not None else {}
    if name == "stoch":
        k = int(params[0]) if params else 14
        d = int(params[1]) if len(params) > 1 else 3
        df_st = pta.stoch(h, l, c, k=k, d=d)
        return _ser(df_st) if df_st is not None else {}
    if name == "stochrsi":
        n = int(params[0]) if params else 14
        df_st = pta.stochrsi(c, length=n)
        return _ser(df_st) if df_st is not None else {}
    if name == "vwap":
        # VWAP requires datetime index; pandas-ta is picky.
        if "dt" in df.columns:
            df2 = df.set_index("dt")
            res = pta.vwap(df2["high"], df2["low"], df2["close"], df2["volume"])
            return _ser(res.reset_index(drop=True), "vwap")
        return _ser(pta.vwap(h, l, c, v), "vwap")
    if name == "supertrend":
        n = int(params[0]) if params else 10
        m = float(params[1]) if len(params) > 1 else 3.0
        df_st = pta.supertrend(h, l, c, length=n, multiplier=m)
        return _ser(df_st) if df_st is not None else {}
    if name == "ichimoku":
        # Returns (visible, leading)
        res = pta.ichimoku(h, l, c)
        if isinstance(res, tuple) and len(res) >= 1:
            return _ser(res[0])
        return {}
    if name == "obv":
        return _ser(pta.obv(c, v), "obv")
    if name == "mfi":
        n = int(params[0]) if params else 14
        return _ser(pta.mfi(h, l, c, v, length=n), f"mfi_{n}")
    if name == "cci":
        n = int(params[0]) if params else 20
        # pandas-ta cci is buggy in some 0.3.14b releases (returns raw typical-price values).
        # Hand-roll: CCI = (TP - SMA(TP, n)) / (0.015 * mean abs deviation).
        tp = (h + l + c) / 3.0
        sma_tp = tp.rolling(n).mean()
        mad = tp.rolling(n).apply(lambda x: (x - x.mean()).abs().mean(), raw=False)
        cci = (tp - sma_tp) / (0.015 * mad)
        return _ser(cci, f"cci_{n}")
    if name == "willr":
        n = int(params[0]) if params else 14
        return _ser(pta.willr(h, l, c, length=n), f"willr_{n}")
    if name == "roc":
        n = int(params[0]) if params else 10
        return _ser(pta.roc(c, length=n), f"roc_{n}")
    if name == "cmf":
        n = int(params[0]) if params else 20
        return _ser(pta.cmf(h, l, c, v, length=n), f"cmf_{n}")
    if name == "psar":
        df_p = pta.psar(h, l, c)
        return _ser(df_p) if df_p is not None else {}
    if name == "kdj":
        # KDJ is a pandas-ta named indicator (not in all versions); fall back to stoch.
        try:
            df_k = pta.kdj(h, l, c, length=int(params[0]) if params else 9)
            return _ser(df_k) if df_k is not None else {}
        except Exception:
            df_st = pta.stoch(h, l, c, k=9, d=3)
            return _ser(df_st) if df_st is not None else {}
    if name == "fib":
        # Fibonacci retracement levels over the last N bars (default 100).
        # Levels are static prices, not a series — encode them as constant series
        # so the output shape stays consistent with other indicators. The agent
        # gets the latest price's position relative to the levels via _ser's
        # last-value snapshot in `snapshot` mode.
        n = int(params[0]) if params else 100
        if len(df) < 2:
            return {}
        window = df.iloc[-n:] if len(df) >= n else df
        hi = float(window["high"].max())
        lo = float(window["low"].min())
        rng = hi - lo
        # Standard retracement ratios measured from high (0%) down to low (100%).
        ratios = {
            "fib_high":  hi,
            "fib_236":   hi - rng * 0.236,
            "fib_382":   hi - rng * 0.382,
            "fib_500":   hi - rng * 0.500,
            "fib_618":   hi - rng * 0.618,
            "fib_786":   hi - rng * 0.786,
            "fib_low":   lo,
        }
        # Position of the latest close inside [low, high], 0..1 (above 1 / below 0
        # if price broke out of the window).
        last_close = float(c.iloc[-1])
        pct_from_low = (last_close - lo) / rng if rng else None
        out: dict[str, list] = {k: [round(v, 6)] * len(df) for k, v in ratios.items()}
        out["fib_pct_from_low"] = [round(pct_from_low, 6) if pct_from_low is not None else None] * len(df)
        out["fib_window_bars"] = [len(window)] * len(df)
        return out
    raise ValueError(f"unknown indicator: {name!r}")


def _series_to_list(s) -> list:
    pd, _ = _deps()
    out = []
    for v in s.tolist():
        if v is None:
            out.append(None)
        elif isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
            out.append(None)
        else:
            out.append(round(float(v), 6) if isinstance(v, (int, float)) else v)
    return out


# ---------- Commands ----------

_DEFAULT_SNAPSHOT = [
    "ema:20", "ema:50", "ema:200",
    "rsi:14",
    "macd",
    "bbands:20:2",
    "atr:14",
    "stochrsi:14",
    "adx:14",
    "obv",
    "cci:20",
]


def cmd_compute(args):
    rows = _load_input(args.input)
    df = _to_df(rows)
    out: dict[str, Any] = {"count": len(df), "indicators": {}}
    if "dt" in df.columns:
        out["timestamps"] = [str(t) for t in df["dt"].tolist()]
    elif "timestamp" in df.columns:
        out["timestamps"] = df["timestamp"].tolist()
    for spec in args.indicators.split(","):
        spec = spec.strip()
        if not spec:
            continue
        try:
            res = _apply(df, spec)
            out["indicators"].update(res)
        except Exception as e:
            out["indicators"][spec] = {"error": f"{type(e).__name__}: {e}"}
    return out


def cmd_snapshot(args):
    """Latest values only — common indicator set for a single-glance read."""
    rows = _load_input(args.input)
    df = _to_df(rows)
    last_close = float(df["close"].iloc[-1])
    out: dict[str, Any] = {
        "n_bars": len(df),
        "last_close": last_close,
        "last_high": float(df["high"].iloc[-1]),
        "last_low": float(df["low"].iloc[-1]),
        "last_volume": float(df["volume"].iloc[-1]),
        "indicators": {},
    }
    if "dt" in df.columns:
        out["last_dt"] = str(df["dt"].iloc[-1])

    specs = (args.indicators.split(",") if args.indicators else _DEFAULT_SNAPSHOT)
    for spec in specs:
        spec = spec.strip()
        if not spec:
            continue
        try:
            res = _apply(df, spec)
            for col, vals in res.items():
                out["indicators"][col] = vals[-1] if vals else None
        except Exception as e:
            out["indicators"][spec] = {"error": f"{type(e).__name__}: {e}"}
    # Quick derived flags.
    def _g(k): return out["indicators"].get(k)
    flags: dict[str, Any] = {}
    rsi = _g("rsi_14")
    if rsi is not None:
        flags["rsi_14_overbought"] = rsi > 70
        flags["rsi_14_oversold"] = rsi < 30
    e50, e200 = _g("ema_50"), _g("ema_200")
    if e50 is not None and e200 is not None:
        flags["golden_cross_state"] = "above" if e50 > e200 else "below"
    out["flags"] = flags
    return out


def cmd_crosses(args):
    """Detect crossover points between two arbitrary indicator series (or close)."""
    if "," not in args.series:
        return {"error": "--series requires two specs separated by comma, e.g. ema:50,ema:200"}
    rows = _load_input(args.input)
    df = _to_df(rows)
    a_spec, b_spec = [s.strip() for s in args.series.split(",", 1)]

    def _one(spec):
        if spec == "close":
            return df["close"].tolist(), "close"
        res = _apply(df, spec)
        # If multi-column, prefer the first.
        col = next(iter(res))
        return res[col], col

    a_vals, a_name = _one(a_spec)
    b_vals, b_name = _one(b_spec)
    crosses = []
    for i in range(1, len(a_vals)):
        a0, a1 = a_vals[i - 1], a_vals[i]
        b0, b1 = b_vals[i - 1], b_vals[i]
        if None in (a0, a1, b0, b1):
            continue
        if (a0 <= b0) and (a1 > b1):
            crosses.append({"bar": i, "direction": "a_up", "a": a1, "b": b1})
        elif (a0 >= b0) and (a1 < b1):
            crosses.append({"bar": i, "direction": "a_down", "a": a1, "b": b1})
    if "dt" in df.columns:
        ts = [str(t) for t in df["dt"].tolist()]
        for c in crosses:
            c["timestamp"] = ts[c["bar"]]
    return {
        "a": a_name, "b": b_name, "count": len(crosses),
        "n_bars": len(df), "crosses": crosses[-args.limit:],
    }


def cmd_list(args):
    """List supported indicator specs (no input needed, no deps)."""
    return {
        "indicators": [
            {"name": "ema",       "spec": "ema:LEN",            "default": "ema:20"},
            {"name": "sma",       "spec": "sma:LEN",            "default": "sma:20"},
            {"name": "wma",       "spec": "wma:LEN",            "default": "wma:20"},
            {"name": "rsi",       "spec": "rsi:LEN",            "default": "rsi:14"},
            {"name": "macd",      "spec": "macd[:FAST:SLOW:SIG]","default": "macd:12:26:9"},
            {"name": "bbands",    "spec": "bbands:LEN:STD",     "default": "bbands:20:2"},
            {"name": "atr",       "spec": "atr:LEN",            "default": "atr:14"},
            {"name": "adx",       "spec": "adx:LEN",            "default": "adx:14"},
            {"name": "stoch",     "spec": "stoch:K:D",          "default": "stoch:14:3"},
            {"name": "stochrsi",  "spec": "stochrsi:LEN",       "default": "stochrsi:14"},
            {"name": "vwap",      "spec": "vwap",               "default": "vwap"},
            {"name": "supertrend","spec": "supertrend:LEN:MULT","default": "supertrend:10:3"},
            {"name": "ichimoku",  "spec": "ichimoku",           "default": "ichimoku"},
            {"name": "obv",       "spec": "obv",                "default": "obv"},
            {"name": "mfi",       "spec": "mfi:LEN",            "default": "mfi:14"},
            {"name": "cci",       "spec": "cci:LEN",            "default": "cci:20"},
            {"name": "willr",     "spec": "willr:LEN",          "default": "willr:14"},
            {"name": "roc",       "spec": "roc:LEN",            "default": "roc:10"},
            {"name": "cmf",       "spec": "cmf:LEN",            "default": "cmf:20"},
            {"name": "psar",      "spec": "psar",               "default": "psar"},
            {"name": "kdj",       "spec": "kdj:LEN",            "default": "kdj:9"},
            {"name": "fib",       "spec": "fib:LOOKBACK",       "default": "fib:100"},
        ],
        "snapshot_default": _DEFAULT_SNAPSHOT,
    }


def main() -> None:
    p = argparse.ArgumentParser(prog="ta.py", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    def _io(sp):
        sp.add_argument("--input", "-i", default="-", help="JSON klines file (or '-' for stdin)")

    pc = sub.add_parser("compute", help="full indicator series aligned to input bars")
    _io(pc)
    pc.add_argument("--indicators", required=True,
                    help="comma-separated specs, e.g. 'rsi:14,macd,ema:20,ema:200,bbands:20:2'")
    pc.set_defaults(func=cmd_compute)

    ps = sub.add_parser("snapshot", help="latest values + a curated default set + quick flags")
    _io(ps)
    ps.add_argument("--indicators", help=f"override default set (default: {','.join(_DEFAULT_SNAPSHOT)})")
    ps.set_defaults(func=cmd_snapshot)

    px = sub.add_parser("crosses", help="crossover detection between two series")
    _io(px)
    px.add_argument("--series", required=True,
                    help="two specs separated by comma, e.g. 'ema:50,ema:200' or 'close,ema:200'")
    px.add_argument("--limit", type=int, default=10, help="return last N crosses")
    px.set_defaults(func=cmd_crosses)

    sub.add_parser("list", help="list supported indicator specs (no deps needed)").set_defaults(func=cmd_list)

    args = p.parse_args()
    try:
        out = args.func(args)
    except SystemExit:
        raise
    except Exception as e:
        die(f"{type(e).__name__}: {e}")
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
