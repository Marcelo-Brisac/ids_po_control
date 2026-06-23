# futures.py — advanced reference

Covers usage beyond the SKILL.md examples.

## Full alias catalogue (30 contracts)

| Group | Aliases | Exchange | Primary | Yahoo `=F` |
|---|---|---|---|---|
| Energy | `CL` `BZ` `NG` `RB` `HO` | NYMEX | Eastmoney (`102`) | yes |
| Precious / base | `GC` `SI` `HG` `PL` `PA` | COMEX / NYMEX | Eastmoney (`101`/`102`) | yes |
| Soft / agri | `SB` `CT` `KC` `CC` | NYBOT | Eastmoney (`108`) | yes |
| Grains | `ZC` `ZW` `ZS` `ZL` `ZM` | CBOT | — | **Yahoo only** |
| Equity index | `ES` `NQ` `YM` `RTY` | CME | — | **Yahoo only** |
| Rates | `ZT` `ZF` `ZN` `ZB` | CBOT | — | **Yahoo only** |
| FX / vol | `DX` `VX` | ICE / CFE | — | **Yahoo only** |

Continuous-month code convention on Eastmoney: `{ROOT}00Y` (`CL00Y`, `GC00Y`).

CN onshore futures live in `cn-markets/scripts/futures.py` (different code
convention: `{root}m` lower or `{ROOT}M` upper).

## Source forcing

```bash
./scripts/futures.py quote CL,GC,ES --source=auto       # default
./scripts/futures.py quote CL,GC --source=yahoo         # skip Eastmoney
./scripts/futures.py quote CL,GC --source=eastmoney     # Eastmoney only (no Yahoo fallback)
```

For CBOT/CME/CFE aliases, `eastmoney` returns errors because these aren't
exposed via `futsseapi`.

## Eastmoney market IDs (`sc`)

| `sc` | Exchange | Path |
|---|---|---|
| 101 | COMEX | `list/COMEX` |
| 102 | NYMEX | `list/NYMEX` |
| 104 | SGX | `list/SGX` |
| 108 | NYBOT | `list/NYBOT` |
| 109 | LME | `list/LME` |
| 111 | TOCOM | `list/TOCOM` |
| 113 | SHFE | `list/SHFE` *(CN — use cn-markets)* |
| 114 | DCE | `list/DCE` *(CN)* |
| 115 | CZCE | `list/CZCE` *(CN)* |
| 142 | INE | `list/INE` *(CN)* |
| 225 | GFEX | `list/GFEX` *(CN)* |

CBOT, CME, ICE, EUREX, OSE all return `{"result":"nodata"}` — not exposed.

## Adding a new contract

Edit `CATALOG` in `scripts/futures.py`. Each entry:
```python
"ALIAS": {"name": "...", "exchange": "...", "sc": ..., "cont": "{root}00Y" or None, "yahoo": "{root}=F" or None}
```

For Eastmoney-covered: provide `sc` + `cont`. For Yahoo-only: `sc=None`, `cont=None`, `yahoo="...=F"`.

## History gap

There's **no history endpoint** for futures in this skill. Eastmoney's
`push2his/qt/stock/kline/get` returns `{"rc":102, "data":null}` for every
futures secid prefix tested. Yahoo's chart endpoint for `=F` is unreliable
across IPs.

If history becomes essential, bring AKShare in for CN onshore (its
`futures_main_sina` + `futures_zh_realtime` pair covers it) and accept the
gap for non-CN. CN onshore history would go in `cn-markets/scripts/futures.py`.

## Burst limit

Eastmoney's futures API shares the same per-IP burst ceiling as the equity
APIs (~20 calls / 5s → multi-minute blackhole). Pace batches; for
Yahoo-only aliases, no Eastmoney load.