# Research: How to Write a Quant Framework That Beats Buy and Hold

Date: 2026-04-15
Status: Complete

## Executive Summary

Three agents researched this from different angles. The consensus: **building a custom
backtesting framework is the wrong first step.** The right first step is testing whether
you have a signal, using existing tools.

## The Honest Answer

Systematic strategies can beat buy-and-hold — sometimes, in specific asset classes, at
certain capacity levels, with substantial infrastructure and discipline. The academic
evidence is strongest for:

- **Cross-sectional momentum** (3–12 month, equities) — most robustly documented anomaly
- **Time-series momentum / trend following** (futures) — multi-decade live track record via CTAs
- **Quality/profitability factor** — most stable, least controversial

But: if you test 1,000 parameter combinations and report the best Sharpe, you've found
noise, not signal. The graveyard of failed quant funds is dominated by exactly this pattern.

## Build vs. Buy: Don't Build a Framework

The devil's advocate made the strongest point: NautilusTrader took a team years to
production-harden. Starting greenfield means you're building infrastructure, not testing
a trading hypothesis. These are different projects with different failure modes.

**Recommended tools for research (no custom framework needed):**

| Purpose | Tool | Why |
|---------|------|-----|
| Rapid signal research | vectorbt | NumPy arrays + Numba JIT, test thousands of variants in seconds |
| Data | yfinance (research only), polygon.io (serious work) | Free vs. reliable |
| Technical indicators | pandas-ta | Pure Python, one-liner indicators |
| Statistical tests | statsmodels | Cointegration, ARIMA, regime models |
| Portfolio construction | PyPortfolioOpt | Mean-variance, risk parity |
| Performance metrics | quantstats | Sharpe, Sortino, drawdown analysis |
| Production (if you get there) | NautilusTrader or Lean | Event-driven, multi-asset, live trading |

## Key Pitfalls

1. **Survivorship bias** — testing on current S&P 500 members ignores all the companies
   that went bankrupt. One study showed momentum CAGR dropping from 26% to 12% when
   delisted companies were added back.

2. **Look-ahead bias** — using information that wouldn't have been available at decision
   time (e.g., today's close to generate today's signal).

3. **Overfitting** — if changing a threshold from 14 to 13 destroys the strategy,
   it's not a signal. Always compute the Deflated Sharpe Ratio to correct for
   multiple testing.

4. **Transaction cost underestimation** — if your strategy relies on returns under
   50 bps per trade, it likely won't survive realistic execution costs.

5. **Regime change** — parameters that worked 2000–2010 may fail 2010–2020 due to
   HFT proliferation, ETF growth, zero-commission trading, and central bank intervention.

## Validation Protocol (Non-Negotiable)

- Walk-forward validation with at least 5 non-overlapping out-of-sample periods
- Minimum 10 years of data to capture different regimes
- Deflated Sharpe Ratio (corrects for number of trials attempted)
- Point-in-time data with delisted securities included
- Realistic slippage (0.05–0.1% for liquid large-caps) and commission modeling
- Stress test against 2000–2002, 2008–2009, 2020 COVID, 2022 rate shock

## The 300-Line Constraint Problem

The devil's advocate flagged that a backtesting engine (event loop, order management,
portfolio accounting, slippage models, data ingestion, analytics) cannot realistically
fit in 300-line modules without fragmenting the design. This is a strong argument for
using vectorbt/NautilusTrader rather than building from scratch.

## Missed Alternatives Worth Exploring

- **Options strategies** (covered calls, cash-secured puts) — more tractable Sharpe
  profile, lower capacity constraints than factor equity
- **Crypto microstructure** — less crowded than equities, higher volatility creates
  more opportunities for systematic approaches
- **Alternative data** — satellite imagery, credit card data, NLP on filings

## Recommended Minimum Viable Product

**Do this before building anything:**

1. One momentum signal (12-month return, cross-sectional)
2. One universe (SPY sector ETFs — XLK, XLF, XLE, etc.)
3. vectorbt backtest with walk-forward split
4. Realistic transaction costs (10 bps round-trip)
5. Compare Sharpe ratio vs. buy-and-hold SPY
6. One plot. One number. Does it work or not?

If that doesn't show edge, no amount of framework engineering will help. If it does,
then graduate to a proper backtesting framework with point-in-time data.

## Key Sources

- Jegadeesh & Titman (1993) — cross-sectional momentum
- Asness, Moskowitz & Pedersen — "Value and Momentum Everywhere"
- Bailey & López de Prado — Deflated Sharpe Ratio
- Gatev, Goetzmann & Rouwenhorst (2006) — pairs trading profitability decay
- Robert Carver, "Systematic Trading" — pysystemtrade methodology
- SG CTA Index — live trend-following track record (4.98% CAGR since 2000)
