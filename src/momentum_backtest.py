"""Momentum-based sector rotation backtest.

Downloads daily data for sector ETFs, computes a 12-month momentum signal,
selects the top 3 sectors monthly, and compares against buy-and-hold QQQM.
"""

from __future__ import annotations

import pandas as pd
import vectorbt as vbt
import yfinance as yf

SECTOR_ETFS: list[str] = [
    "XLK",
    "XLF",
    "XLE",
    "XLV",
    "XLI",
    "XLC",
    "XLY",
    "XLP",
    "XLB",
    "XLRE",
    "XLU",
]
BENCHMARK_TICKER: str = "QQQM"
DEFAULT_START: str = "2018-01-01"
DEFAULT_FEES: float = 0.0005  # 5 bps per side = 10 bps round-trip


def download_data(tickers: list[str], start: str, end: str | None = None) -> pd.DataFrame:
    """Download adjusted close prices for the given tickers.

    Args:
        tickers: List of ticker symbols to download.
        start: Start date string (YYYY-MM-DD).
        end: Optional end date string. Defaults to today.

    Returns:
        DataFrame indexed by date with one column per ticker.
    """
    data = yf.download(tickers, start=start, end=end, auto_adjust=True)

    if isinstance(data.columns, pd.MultiIndex):
        prices = data["Close"]
    else:
        # Single ticker returns flat columns
        prices = data[["Close"]].rename(columns={"Close": tickers[0]})

    # Drop tickers with no data at all
    prices = prices.dropna(how="all", axis=1)
    return prices


def compute_momentum_signals(
    prices: pd.DataFrame, lookback_days: int = 252, top_n: int = 3
) -> pd.DataFrame:
    """Compute monthly rebalance weights based on trailing momentum.

    On each rebalance date (first trading day of the month), ranks sectors by
    trailing return over *lookback_days* and assigns equal weight to the top-N.
    Non-rebalance rows are NaN (hold previous weights per vectorbt convention).

    Args:
        prices: Daily close prices, one column per sector.
        lookback_days: Number of trading days for the trailing return.
        top_n: How many top sectors to hold.

    Returns:
        DataFrame of target weights (same shape as *prices*).
    """
    trailing_returns = prices.pct_change(lookback_days)

    # Rebalance on first trading day of each month
    month_periods = prices.index.to_period("M")
    is_rebalance = ~month_periods.duplicated()

    weights = pd.DataFrame(index=prices.index, columns=prices.columns, dtype=float)

    for i, rebalance in enumerate(is_rebalance):
        if not rebalance:
            continue

        row = trailing_returns.iloc[i]
        valid = row.dropna()

        # Warm-up guard: skip if insufficient data
        if len(valid) < top_n:
            continue

        top_tickers = valid.nlargest(top_n).index
        w = 1.0 / top_n
        for ticker in prices.columns:
            weights.iloc[i, weights.columns.get_loc(ticker)] = w if ticker in top_tickers else 0.0

    return weights


def run_backtest(
    prices: pd.DataFrame, weights: pd.DataFrame, fees: float = DEFAULT_FEES
) -> vbt.Portfolio:
    """Run the momentum strategy backtest using vectorbt.

    Args:
        prices: Daily close prices for sector ETFs.
        weights: Target weight matrix from compute_momentum_signals.
        fees: Per-side transaction fee (0.0005 = 5 bps).

    Returns:
        vectorbt Portfolio object with backtest results.
    """
    return vbt.Portfolio.from_orders(
        close=prices,
        size=weights,
        size_type="targetpercent",
        group_by=True,
        cash_sharing=True,
        call_seq="auto",
        fees=fees,
        freq="1D",
    )


def compare_results(
    strategy_pf: vbt.Portfolio, benchmark_pf: vbt.Portfolio
) -> dict[str, dict[str, float]]:
    """Extract and compare key performance metrics.

    Args:
        strategy_pf: Portfolio object for the momentum strategy.
        benchmark_pf: Portfolio object for the buy-and-hold benchmark.

    Returns:
        Dict with 'strategy' and 'benchmark' sub-dicts containing
        sharpe_ratio, cagr, and max_drawdown.
    """

    def _extract(pf: vbt.Portfolio) -> dict[str, float]:
        sharpe = pf.sharpe_ratio()
        cagr = pf.annualized_return()
        mdd = pf.max_drawdown()
        # Handle both scalar and Series returns
        if isinstance(sharpe, pd.Series):
            sharpe = sharpe.iloc[0]
        if isinstance(cagr, pd.Series):
            cagr = cagr.iloc[0]
        if isinstance(mdd, pd.Series):
            mdd = mdd.iloc[0]
        return {
            "sharpe_ratio": float(sharpe),
            "cagr": float(cagr),
            "max_drawdown": float(mdd),
        }

    return {
        "strategy": _extract(strategy_pf),
        "benchmark": _extract(benchmark_pf),
    }


def main() -> None:
    """Run the full momentum sector rotation backtest and print results."""
    all_tickers = [*SECTOR_ETFS, BENCHMARK_TICKER]
    all_prices = download_data(all_tickers, start=DEFAULT_START)

    sector_prices = all_prices[[t for t in SECTOR_ETFS if t in all_prices.columns]]
    benchmark_prices = all_prices[[BENCHMARK_TICKER]]

    weights = compute_momentum_signals(sector_prices)
    strategy_pf = run_backtest(sector_prices, weights)
    benchmark_pf = vbt.Portfolio.from_holding(benchmark_prices, freq="1D")

    results = compare_results(strategy_pf, benchmark_pf)

    print("\n" + "=" * 60)
    print("Momentum Sector Rotation Backtest Results")
    print("=" * 60)
    print(f"{'Metric':<20} {'Strategy':>15} {'QQQM B&H':>15}")
    print("-" * 60)
    print(
        f"{'Sharpe Ratio':<20} "
        f"{results['strategy']['sharpe_ratio']:>15.3f} "
        f"{results['benchmark']['sharpe_ratio']:>15.3f}"
    )
    print(
        f"{'CAGR':<20} {results['strategy']['cagr']:>14.1%}  {results['benchmark']['cagr']:>14.1%} "
    )
    print(
        f"{'Max Drawdown':<20} "
        f"{results['strategy']['max_drawdown']:>14.1%}  "
        f"{results['benchmark']['max_drawdown']:>14.1%} "
    )
    print("=" * 60)
    print("\nLookback: 252 trading days (~12 months)")
    print("Top sectors held: 3 (equal-weight)")
    print("Rebalance: monthly (first trading day)")
    print("Transaction costs: 10 bps round-trip")
    print(f"Period: {DEFAULT_START} to present")


if __name__ == "__main__":
    main()
