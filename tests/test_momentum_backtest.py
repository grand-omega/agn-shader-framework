"""Tests for momentum_backtest module."""

from __future__ import annotations

from unittest.mock import patch

import numpy as np
import pandas as pd

from momentum_backtest import compute_momentum_signals, download_data


def _make_prices(n_days: int = 300, n_tickers: int = 5) -> pd.DataFrame:
    """Create deterministic synthetic price data.

    Ticker_0 has the highest daily return, Ticker_1 second highest, etc.
    This makes momentum ranking predictable.
    """
    dates = pd.bdate_range("2020-01-01", periods=n_days, freq="B")
    data = {}
    for i in range(n_tickers):
        daily_return = 1.001 + (n_tickers - i) * 0.0005
        data[f"Ticker_{i}"] = 100.0 * daily_return ** np.arange(n_days)
    return pd.DataFrame(data, index=dates)


class TestComputeMomentumSignals:
    """Tests for the compute_momentum_signals function."""

    def test_top_n_selection_count(self) -> None:
        """Exactly top_n tickers get non-zero weight on rebalance days."""
        prices = _make_prices(n_days=300, n_tickers=5)
        weights = compute_momentum_signals(prices, lookback_days=252, top_n=3)

        rebalance_rows = weights.dropna(how="all")
        for _, row in rebalance_rows.iterrows():
            nonzero = (row > 0).sum()
            assert nonzero == 3

    def test_correct_tickers_selected(self) -> None:
        """With deterministic data, top-3 are always Ticker_0, Ticker_1, Ticker_2."""
        prices = _make_prices(n_days=300, n_tickers=5)
        weights = compute_momentum_signals(prices, lookback_days=252, top_n=3)

        rebalance_rows = weights.dropna(how="all")
        for _, row in rebalance_rows.iterrows():
            selected = row[row > 0].index.tolist()
            assert set(selected) == {"Ticker_0", "Ticker_1", "Ticker_2"}

    def test_non_rebalance_days_are_nan(self) -> None:
        """Rows that are not the first trading day of a month should be all NaN."""
        prices = _make_prices(n_days=300, n_tickers=5)
        weights = compute_momentum_signals(prices, lookback_days=252, top_n=3)

        month_periods = prices.index.to_period("M")
        is_rebalance = ~month_periods.duplicated()

        for i, rebal in enumerate(is_rebalance):
            if not rebal:
                assert weights.iloc[i].isna().all()

    def test_unselected_tickers_are_zero(self) -> None:
        """On rebalance days, non-selected tickers have weight 0."""
        prices = _make_prices(n_days=300, n_tickers=5)
        weights = compute_momentum_signals(prices, lookback_days=252, top_n=3)

        rebalance_rows = weights.dropna(how="all")
        for _, row in rebalance_rows.iterrows():
            assert (row == 0).sum() == 2  # 5 tickers - 3 selected = 2 zeros

    def test_weights_sum_to_one(self) -> None:
        """On every rebalance day, weights sum to 1.0."""
        prices = _make_prices(n_days=300, n_tickers=5)
        weights = compute_momentum_signals(prices, lookback_days=252, top_n=3)

        rebalance_rows = weights.dropna(how="all")
        for _, row in rebalance_rows.iterrows():
            assert abs(row.sum() - 1.0) < 1e-10

    def test_tie_handling(self) -> None:
        """All sectors with identical returns still produce exactly top_n selections."""
        dates = pd.bdate_range("2020-01-01", periods=300, freq="B")
        # All tickers have identical returns
        base = 100.0 * 1.001 ** np.arange(300)
        data = {f"T{i}": base.copy() for i in range(5)}
        prices = pd.DataFrame(data, index=dates)

        weights = compute_momentum_signals(prices, lookback_days=252, top_n=3)
        rebalance_rows = weights.dropna(how="all")
        for _, row in rebalance_rows.iterrows():
            assert (row > 0).sum() == 3

    def test_warmup_guard(self) -> None:
        """Rebalance dates before lookback window fills produce no weights (all NaN)."""
        prices = _make_prices(n_days=300, n_tickers=5)
        weights = compute_momentum_signals(prices, lookback_days=252, top_n=3)

        # First 252 days should have no valid rebalance weights
        month_periods = prices.index[:252].to_period("M")
        is_rebalance_early = ~month_periods.duplicated()

        for i, rebal in enumerate(is_rebalance_early):
            if rebal:
                assert weights.iloc[i].isna().all(), (
                    f"Day {i} is in warm-up but has non-NaN weights"
                )


class TestDownloadData:
    """Tests for the download_data function."""

    @patch("momentum_backtest.yf.download")
    def test_single_ticker(self, mock_download: object) -> None:
        """Single ticker returns DataFrame with ticker as column name."""
        dates = pd.bdate_range("2023-01-01", periods=5)
        mock_download.return_value = pd.DataFrame(
            {"Close": [100.0, 101.0, 102.0, 103.0, 104.0]},
            index=dates,
        )

        result = download_data(["AAPL"], start="2023-01-01")
        assert list(result.columns) == ["AAPL"]
        assert len(result) == 5

    @patch("momentum_backtest.yf.download")
    def test_multiple_tickers(self, mock_download: object) -> None:
        """Multiple tickers return MultiIndex columns, resolved to flat columns."""
        dates = pd.bdate_range("2023-01-01", periods=5)
        arrays = [
            ["Close", "Close", "Open", "Open"],
            ["AAPL", "MSFT", "AAPL", "MSFT"],
        ]
        tuples = list(zip(*arrays, strict=True))
        index = pd.MultiIndex.from_tuples(tuples)
        data = pd.DataFrame(
            np.random.default_rng(42).random((5, 4)),
            index=dates,
            columns=index,
        )
        mock_download.return_value = data

        result = download_data(["AAPL", "MSFT"], start="2023-01-01")
        assert set(result.columns) == {"AAPL", "MSFT"}

    @patch("momentum_backtest.yf.download")
    def test_nan_column_dropped(self, mock_download: object) -> None:
        """Columns that are entirely NaN get dropped."""
        dates = pd.bdate_range("2023-01-01", periods=5)
        arrays = [["Close", "Close"], ["AAPL", "BAD"]]
        tuples = list(zip(*arrays, strict=True))
        index = pd.MultiIndex.from_tuples(tuples)
        data = pd.DataFrame(
            {
                ("Close", "AAPL"): [100.0, 101.0, 102.0, 103.0, 104.0],
                ("Close", "BAD"): [np.nan, np.nan, np.nan, np.nan, np.nan],
            },
            index=dates,
        )
        data.columns = index
        mock_download.return_value = data

        result = download_data(["AAPL", "BAD"], start="2023-01-01")
        assert list(result.columns) == ["AAPL"]
