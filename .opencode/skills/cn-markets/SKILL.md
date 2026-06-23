---
name: cn-markets
description: >
  Mainland-China market-data lookups. Use when the user wants: (1) a quote
  or price history for an A-share, HK name, CN index, or CN onshore
  commodity future, (2) A-share filings data (财务, 业绩预告, 龙虎榜,
  大宗交易, 解禁, 股东, 增减持, 回购, 分红, 新股), (3) CN flow signals
  (北向资金, 涨跌停, 行业/题材板块), (4) CN ETF or 可转债 list/quote,
  (5) CN ETF or CFFEX index-options data, or (6) CN macro series (CPI,
  PPI, GDP, M2, PMI, 社融, LPR, SHIBOR, 国债收益率).
---

# CN Markets

Five scripts. Price tape + CN signals are stdlib-only. Research, options, and
macro use `akshare` (lazy-imported — only the path that needs it will fail
without it, with an install hint).

| Script | Deps | Covers |
|---|---|---|
| `scripts/equity.py`   | stdlib | A-share + HK quote/history, indices, search, 北向, 涨跌停, 行业/题材板块 |
| `scripts/futures.py`  | stdlib | 18 CN onshore commodity-futures aliases (SHFE/DCE/CZCE/INE/GFEX) |
| `scripts/research.py` | `akshare` | A-share IS/BS/CF, 业绩预告/快报/披露计划, 龙虎榜, 大宗交易, 解禁, 股东户数, 高管增减持, 回购, 分红, 新股, ETF, 可转债 |
| `scripts/options.py`  | `akshare` | CN ETF options (50ETF, 300ETF, 500ETF, 科创50ETF) + CFFEX index options (IO, MO, HO) |
| `scripts/macro.py`    | `akshare` | CN CPI/PPI/GDP/M0M1M2/PMI/社融/财政/LPR/SHIBOR/工业增加值/零售/固定资产/储备金率/国债收益率 |

Install akshare only if you'll use research, options, or macro:

```bash
# At the skill root (where pyproject.toml + uv.lock live)
uv sync --frozen       # one-time, installs exactly what's locked
```

`--frozen` skips re-resolution and installs straight from `uv.lock`
— fast and reproducible. If it errors with "lock out of date", the
maintainer needs to re-lock; don't drop `--frozen` to mask it.

**Always invoke akshare-backed scripts via `uv run`** (`uv run
scripts/research.py …`). The shebang is plain `#!/usr/bin/env
python3`, so `./scripts/research.py` will pick the system
interpreter and fail with `akshare not installed` even after
`uv sync`. Stdlib-only scripts (`equity.py`, `futures.py`) can be
run either way.

Scripts emit `{"error":"akshare not installed","install":"..."}` on those
paths when missing — stdlib paths run unaffected.

## CLI

### equity.py (stdlib)

```bash
./scripts/equity.py quote CODE[,CODE,...]              # batched A-share + HK
./scripts/equity.py history CODE --days N              # daily OHLCV (also --from --to)
./scripts/equity.py index NAME[,NAME,...]              # HS300, CHINEXT, HSI, HSCEI, HSTECH, ...
./scripts/equity.py search "QUERY"                     # by name / code / pinyin
./scripts/equity.py northbound                         # Stock Connect flow summary (today only)
./scripts/equity.py limit-up                           # today's 涨停股
./scripts/equity.py limit-down                         # today's 跌停股
./scripts/equity.py industry                           # 行业板块 ranked
./scripts/equity.py concept                            # 题材板块 ranked
```

Codes: 6-digit A-share (`600519`, `000001`, `300750`); 5-digit HK (`00700`).
A-share quotes batch in a single HTTP via Sina (`hk{code}` for HK).

→ Symbol guide, source fallback chain, board secid prefixes: [references/equity.md](references/equity.md)

### futures.py (stdlib)

```bash
./scripts/futures.py quote ALIAS[,ALIAS,...]    # CN main-continuous (主连)
./scripts/futures.py list                       # supported CN onshore aliases
```

Aliases (case-sensitive): SHFE `cu` `al` `au` `ag` `rb` `hc`; DCE `i` `m` `p` `c`; CZCE `SR` `CF` `TA` `MA` `FG` `SA`; INE `sc`; GFEX `lc`.

→ Continuous-month code conventions, exchange routing: [references/futures.md](references/futures.md)

### research.py (akshare)

Fundamentals:
```bash
uv run scripts/research.py fundamentals CODE [--quarterly]   # IS + BS + CF (Eastmoney F10)
uv run scripts/research.py forecast [--date YYYYMMDD]        # 业绩预告
uv run scripts/research.py flash [--date YYYYMMDD]           # 业绩快报
uv run scripts/research.py report-calendar [--date YYYYMMDD] # 财报披露计划
```

Events:
```bash
uv run scripts/research.py lhb [--date YYYYMMDD]             # 龙虎榜 daily
uv run scripts/research.py lhb-stock CODE                    # 龙虎榜 history for one stock
uv run scripts/research.py block-trade [--date YYYYMMDD]     # 大宗交易
uv run scripts/research.py unlock [--month YYYYMM]           # 限售解禁日历
uv run scripts/research.py shareholder-count CODE            # 股东户数 history
uv run scripts/research.py insider-trade [--date YYYYMMDD]   # 高管增减持
uv run scripts/research.py buyback                           # 回购实施
uv run scripts/research.py dividend [--code CODE]            # 分红送转
```

Primary market + ETF + 可转债:
```bash
uv run scripts/research.py ipo-calendar
uv run scripts/research.py ipo-winning [--year YYYY]
uv run scripts/research.py etf-list
uv run scripts/research.py etf-quote CODE
uv run scripts/research.py cb-list
uv run scripts/research.py cb-quote CODE
```

→ Field semantics, AKShare function mapping, gotchas: [references/research.md](references/research.md)

### options.py (akshare)

```bash
uv run scripts/options.py underlyings                       # list ETF + CFFEX index option underlyings (no akshare needed)
uv run scripts/options.py expiries CODE                     # listed expiry months
uv run scripts/options.py chain CODE --expiry M             # full chain (M accepts YYYYMM or YYMM)
uv run scripts/options.py pcr CODE                          # put/call ratio + IV summary
```

→ Underlying coverage, exchange routing: [references/options.md](references/options.md)

### macro.py (akshare)

```bash
uv run scripts/macro.py cpi
uv run scripts/macro.py ppi
uv run scripts/macro.py gdp
uv run scripts/macro.py m0m1m2
uv run scripts/macro.py pmi-mfg          # 制造业 PMI
uv run scripts/macro.py pmi-non-mfg      # 非制造业 PMI
uv run scripts/macro.py pmi-caixin       # 财新 PMI
uv run scripts/macro.py social-financing
uv run scripts/macro.py lpr
uv run scripts/macro.py shibor
uv run scripts/macro.py treasury-yield   # CN 国债收益率曲线
uv run scripts/macro.py industrial / retail / fixed-asset / reserve-rate / fiscal
```

→ Series semantics, frequency, units: [references/macro.md](references/macro.md)

## Source strategy

| Need | Primary | Fallback |
|---|---|---|
| A-share quote (batched) | Sina `hq.sinajs.cn` (1 HTTP for N) | Eastmoney → Tencent |
| A-share/HK history (kline) | Eastmoney `push2his` | Sina `getKLineData` (A only) → Tencent `fqkline` / `hkfqkline` |
| HK quote | Eastmoney (`116.*`) | Sina (`hk{code}`) → Tencent → Yahoo (`{code}.HK`) |
| CN/HK indices | Eastmoney (`1.000xxx`, `100.HSI`, ...) | Sina (`s_*`, `int_hangseng`) → Tencent (`q=sh*`, `hkHSI`) → Yahoo (HK only) |
| CN-only signals (北向/涨跌停/板块) | Eastmoney `clist`/`kamt` | push2delay shard (~15min lag) for clist; **none** for kamt |
| CN onshore futures | Eastmoney `futsseapi/static` | — |
| Fundamentals / events / ETF / CB | AKShare (wraps Eastmoney F10 + 巨潮 + JSL + 同花顺) | — |
| CN macro | AKShare (wraps 国家统计局 + 央行) | — |
| CN options | AKShare (wraps SSE/SZSE/CFFEX via Sina+Eastmoney) | — |

→ Endpoint catalogue + Stock-Connect & 龙虎榜 backlog: [references/sources.md](references/sources.md)

## Rate limits

Eastmoney and Sina throttle by IP with multi-minute windows.
On failure (RemoteDisconnected, HTTP 429), **don't retry** —
return the error and move on. `limit-up` / `limit-down` /
`industry` / `concept` auto-fall-back to `push2delay.eastmoney.com`
(~15-min lag) when `push2` is blocked.
