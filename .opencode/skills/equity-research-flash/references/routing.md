# Data routing — which workspace skill backs which need

The complete registry of data sources used by every workflow in this
skill. When a methodology doc says "pull income statement" or "get
the curve", look up the need below and call the workspace skill named
in the right column.

If a need is not in any table, it is a **data gap** — see
"Known data gaps" at the bottom. Disclose the gap, do not fabricate.

---

## Equities — US

| Need | Workspace skill | Notes |
|---|---|---|
| Quote, history, daily/intraday | `global-markets` | Nasdaq → Yahoo → Eastmoney chain |
| Fundamentals (IS / BS / CF, annual + quarterly) | `global-markets` | Yahoo via yfinance |
| Company snapshot (sector / margins / ratios) | `global-markets` | Yahoo via yfinance |
| Holders (major / institutional / mutual fund) | `global-markets` | Yahoo via yfinance |
| Insider transactions + roster | `global-markets` | Yahoo via yfinance |
| Analyst recs, price targets, up/downgrades | `global-markets` | Yahoo via yfinance |
| Earnings + revenue estimates, EPS trend | `global-markets` | Yahoo via yfinance |
| Per-name calendar (next earnings + dividend) | `global-markets` | Yahoo via yfinance |
| Earnings calendar (window across all listings) | `global-markets` | Nasdaq |
| News headlines | `global-markets` | Yahoo via yfinance |
| Dividend / split / capital-gains history | `global-markets` | Yahoo via yfinance |
| Options chains, Greeks, IV term structure | `global-markets` | Yahoo via yfinance |

## Equities — CN (A-share + HK)

| Need | Workspace skill |
|---|---|
| A-share / HK quote, history, indices | `cn-markets` |
| 北向/南向资金, 涨跌停, 行业/题材板块 | `cn-markets` |
| A-share fundamentals (IS / BS / CF) | `cn-markets` |
| 业绩预告, 龙虎榜, 大宗交易, 解禁, 股东户数, 增减持, 回购, 分红, 新股 | `cn-markets` |
| CN ETF / 可转债 list + quote | `cn-markets` |
| CN ETF options (50/300/500/科创50 ETF), CFFEX index options | `cn-markets` |

## Equities — JP / DE / KR / global indices

| Need | Workspace skill |
|---|---|
| Quote, history, search | `global-markets` |

## Futures

| Need | Workspace skill |
|---|---|
| Global energy / metals / soft / grain / index / rate futures | `global-markets` |
| CN onshore commodity futures (SHFE / DCE / CZCE / INE / GFEX) | `cn-markets` |

## FX

| Need | Workspace skill |
|---|---|
| FX latest, history, conversion (ECB-sourced) | `macro-rates-fx` |
| FX spot snapshot alongside US equity flow | `global-markets` |

## Rates

| Need | Workspace skill |
|---|---|
| US Treasury yield curve (cash, EOD) | `macro-rates-fx` |
| US per-tenor history (1M…30Y) | `macro-rates-fx` |
| US Treasury futures (ZT/ZF/ZN/ZB) | `global-markets` |
| Curve spreads (10Y-2Y, 10Y-3M) | `macro-rates-fx` (FRED) |
| Credit OAS (HY / IG) | `macro-rates-fx` (FRED) |
| CN 国债收益率曲线, LPR, SHIBOR | `cn-markets` |

## Macro

| Need | Workspace skill |
|---|---|
| US CPI / PCE / NFP / unemployment / GDP / IP / retail / housing / M2 / WALCL / Fed funds / DXY / sentiment / VIX | `macro-rates-fx` (FRED, key required) |
| CN CPI / PPI / GDP / M0M1M2 / 社融 / 财政 / PMI / 工业增加值 / 零售 / 固定资产 / 储备金率 | `cn-markets` |

## Crypto

| Need | Workspace skill |
|---|---|
| Spot quote / klines (any Binance pair) | `crypto-markets` |
| Top-N mcap, dominance, trending, F&G | `crypto-markets` |
| Perp funding / OI / LSR (Binance/Bybit/OKX) | `crypto-markets` |
| BTC network stats | `crypto-markets` |
| DeFi TVL, protocols, yield pools, fees/revenue, stablecoins | `crypto-markets` |
| DEX pairs / token search / contract metadata | `crypto-markets` |
| Crypto news (RSS) | `crypto-markets` |

## Technical analysis (asset-agnostic)

| Need | Workspace skill |
|---|---|
| EMA / SMA / RSI / MACD / BBands / ATR / ADX / Stoch / VWAP / SuperTrend / Ichimoku / OBV / MFI / CCI / etc. | `ta-engine` — consumes OHLCV from any of the above |

## SEC filings (US)

| Need | Source | Notes |
|---|---|---|
| 10-K / 10-Q / 8-K / DEF 14A / S-1 / 13F / Form 4 / 13G/13D full text | `scripts/edgar.py` (this skill) | UA-gated EDGAR; `cik <ticker>` → CIK, `fetch <url>` → body |
| Cross-company fundamentals at scale (one GAAP concept × all filers × period) | `scripts/edgar.py fetch` + XBRL Frames | `data.sec.gov/api/xbrl/frames/us-gaap/<Concept>/USD/CY<Y>Q<Q>.json` — reported scales vary across filers, infer from magnitude |
| Earnings press release + prepared commentary | `scripts/edgar.py fetch` of 8-K Ex 99.1 | Item 2.02 8-K → exhibit `99.1`. Close cousin to transcript, **not** the full Q&A (see gaps) |
| Filer-chosen peer group | `scripts/edgar.py fetch` of DEF 14A or 10-K Item 5 | DEF 14A comp-benchmark table is most reliable; 10-K stock-performance graph sometimes only names indices |

## Alt-data (US)

| Need | Source | Notes |
|---|---|---|
| Federal contract awards (recipient, $ amount, agency, scope, dates) | `scripts/usaspending.py` (this skill) | Keyless `api.usaspending.gov`; `awards <recipient>` defaults to contracts last 24 months. Relevant for defense primes / govtech / public-payor healthcare. |

---

## Known data gaps (relative to vendored methodology)

These needs come up in the methodology docs but have **no workspace
skill backing them yet**. Tell the user explicitly when you hit one —
don't invent or hallucinate the data.

| Gap | Methodology docs that lean on it |
|---|---|
| **Earnings-call transcripts** (full Q&A with analysts) | `earnings-preview`, `earnings-analysis`, `earnings-scorecard`, `morning-note`, `thesis-tracker`, `thesis-check` |
| **Curated analyst-grade peer comp group** (judgment-baked 8–12 names; not the broader SIC cohort or filer-chosen list, both of which are closeable above) | `sector-overview`, `business-model`, `management`, valuation comps |
| **Customer / supplier ontology** beyond the >10%-of-revenue concentration that 10-K Item 1 requires | `sector-overview`, `business-model`, `management` |
| **Alt-data**: hiring, patents, customs flows | `idea-generation` (alt-play lenses), upstream `supply-chain` / `trade-flows` (not vendored — see `community/NOTICE.md`) |

If a deliverable depends on a gap item, lead the response with: *"To
write a publication-grade [X] I need [full Q&A transcript | curated
comp group | …] which this skill set does not currently source. I can
[partial deliverable using available data] — or, if you can paste the
[transcript / comp group], I can do the full analysis."*

Do not fabricate. Do not paper over the gap with general knowledge.
