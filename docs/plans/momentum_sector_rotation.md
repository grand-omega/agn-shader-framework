# Plan: Momentum-Based Sector Rotation Strategy

Date: 2026-04-15
Status: Draft

## Problem statement

Build a momentum-based sector rotation backtest that each month selects the
top 3 sector ETFs by trailing 12-month return, equal-weights them, and
compares performance against a buy-and-hold QQQM baseline. The strategy
should account for realistic transaction costs (10 bps round-trip).

## Research findings

### Prior implementation

A previous implementation existed at commit `55cab0d` and was removed during
refactoring. That cycle completed successfully (7/7 requirements met, 0 ruff
violations, 53% test coverage). Key lessons from the feedback log:

- Splitting pure signal-generation logic from portfolio construction keeps the
  most critical code fully testable without heavy framework dependencies.
- The warm-up guard (skipping rebalance dates before the lookback window fills)
  is the critical edge case -- worth testing explicitly.
- 53% file-level coverage is acceptable when the untested portion is
  intentionally excluded (vectorbt portfolio construction) per plan constraints.

### vectorbt

- `Portfolio.from_orders()` supports multi-asset rebalancing via
  `size_type='targetpercent'` with `cash_sharing=True` and
  `call_seq='auto'` (sells before buys).
- `fees` parameter is per-side: pass `0.0005` for 10 bps round-trip (5 bps
  each side, applied to both entry and exit).
- `Portfolio.from_holding(close)` creates a buy-and-hold baseline.
- Stats: `pf.sharpe_ratio()`, `pf.annualized_return()`, `pf.max_drawdown()`.

### yfinance

- `yf.download(tickers, start, end, auto_adjust=True)` returns adjusted prices.
- Multiple tickers produce MultiIndex columns `(Price, Ticker)`.
- Access close prices: `data['Close']` returns DataFrame with ticker columns.

### Rebalance mechanics

- Monthly rebalance mask: `~prices.index.to_period('M').duplicated()` gives
  True on the first trading day of each month.
- Momentum signal: `prices.pct_change(252)` gives trailing ~12-month return.
- Weight matrix: NaN = hold previous allocation (vectorbt convention).

## Dependencies needed

```bash
uv add vectorbt yfinance
```

If numpy 2.x compatibility issues arise with vectorbt/numba:

```bash
uv add "numpy<2.0"
```

## File structure

```
src/momentum_backtest.py          # single module, all logic
tests/test_momentum_backtest.py   # tests (mock yfinance, synthetic data)
```

## Module design

### Constants

```python
SECTOR_ETFS: list[str] = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLC", "XLY", "XLP", "XLB", "XLRE", "XLU"]
BENCHMARK_TICKER: str = "QQQM"
DEFAULT_START: str = "2018-01-01"
DEFAULT_FEES: float = 0.0005  # 5 bps per side = 10 bps round-trip
```

### Functions

#### `download_data(tickers: list[str], start: str, end: str | None = None) -> pd.DataFrame`

- Wraps `yf.download()` with `auto_adjust=True`.
- Handles single-ticker vs multi-ticker MultiIndex column formats.
- Drops columns that are entirely NaN (delisted/missing tickers).
- Returns DataFrame indexed by date, one column per ticker.

#### `compute_momentum_signals(prices: pd.DataFrame, lookback_days: int = 252, top_n: int = 3) -> pd.DataFrame`

- Computes trailing returns via `prices.pct_change(lookback_days)`.
- On each rebalance date (first trading day of month), ranks sectors by
  trailing return and assigns `1/top_n` weight to top-N, `0` to others.
- Non-rebalance rows are NaN (hold previous weights).
- **Warm-up guard**: skips rebalance dates where trailing return has
  insufficient data (all NaN or fewer than `top_n` valid values).
- This is a pure function -- no side effects, fully testable.

#### `run_backtest(prices: pd.DataFrame, weights: pd.DataFrame, fees: float = DEFAULT_FEES) -> vbt.Portfolio`

- Calls `vbt.Portfolio.from_orders()` with:
  - `size=weights, size_type="targetpercent"`
  - `group_by=True, cash_sharing=True, call_seq="auto"`
  - `fees=fees, freq="1D"`
- Returns the Portfolio object.

#### `compare_results(strategy_pf: vbt.Portfolio, benchmark_pf: vbt.Portfolio) -> dict[str, dict[str, float]]`

- Extracts from each portfolio: `sharpe_ratio`, `annualized_return` (CAGR),
  `max_drawdown`.
- Handles both scalar and Series return types from vectorbt stats methods.
- Returns `{"strategy": {...}, "benchmark": {...}}`.

#### `main() -> None`

- Downloads all sector ETFs + QQQM.
- Splits into sector prices and benchmark prices.
- Computes momentum signals and runs backtest.
- Runs QQQM buy-and-hold via `Portfolio.from_holding()`.
- Prints formatted comparison table to stdout.
- Guarded by `if __name__ == "__main__"`.

## Testing strategy

### File: `tests/test_momentum_backtest.py`

All tests use synthetic data or mocked yfinance -- no network calls.

#### Synthetic price data helper

```python
def _make_prices(n_days: int = 300, n_tickers: int = 5) -> pd.DataFrame
```

Creates deterministic price series where Ticker_0 has highest daily return,
Ticker_1 second highest, etc. This makes the ranking predictable.

#### Test cases for `compute_momentum_signals`

1. **Top-N selection**: verify exactly `top_n` tickers get weight `1/top_n`.
2. **Correct tickers selected**: with deterministic synthetic data, verify
   the top-3 are always T0, T1, T2.
3. **Non-rebalance days are NaN**: rows not on first-of-month are all NaN.
4. **Unselected tickers are zero**: on rebalance days, non-selected tickers
   have weight 0.
5. **Weights sum to 1.0**: on every rebalance day.
6. **Tie handling**: all sectors with identical returns still produce exactly
   `top_n` selections (nlargest handles ties).
7. **Warm-up guard**: rebalance dates before 252 days produce no weights
   (all NaN).

#### Test cases for `download_data`

1. **Single ticker**: mock returns non-MultiIndex DataFrame, verify column
   renamed correctly.
2. **Multiple tickers**: mock returns MultiIndex, verify both columns present.
3. **NaN column dropped**: mock with one all-NaN column, verify it's removed.

All tests mock `momentum_backtest.yf.download` via `unittest.mock.patch`.

#### What NOT to test

- `run_backtest` and `compare_results` are thin wrappers around vectorbt.
  Testing them would just test vectorbt itself. Per prior cycle feedback,
  53% file-level coverage is acceptable with this intentional exclusion.

## Risks and mitigations

| Risk | Mitigation |
|------|-----------|
| vectorbt + numpy 2.x incompatibility | Pin `numpy<2.0` if install fails |
| yfinance rate limiting or data gaps | `dropna(how="all", axis=1)` handles missing tickers |
| vectorbt API changes | Pin version: `uv add vectorbt==0.28.5` if needed |
| First 12 months are warm-up | Document in output; warm-up guard in code |

## Success criteria

1. `uv run python src/momentum_backtest.py` prints Sharpe ratio, CAGR, and
   max drawdown for both strategy and QQQM to stdout.
2. `uv run pytest tests/test_momentum_backtest.py` -- all tests pass.
3. `uv run ruff check .` -- zero violations.
4. Strategy uses 12-month (252 trading day) lookback, top-3 selection,
   monthly rebalance on first trading day.
5. Transaction costs of 10 bps round-trip applied.
6. Backtest covers 2018-01-01 to present.
7. `src/momentum_backtest.py` is under 300 lines.
