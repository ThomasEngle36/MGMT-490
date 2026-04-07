# Portfolio Optimizer (Path A)

This Streamlit app builds optimized portfolios using historical market data and constrained optimization.

## Features
- Accepts 5-15 stock tickers
- Downloads historical prices from Yahoo Finance via `yfinance`
- Computes expected annual return and annualized covariance
- Optimizes portfolio using:
  - Max Sharpe
  - Min Variance
  - Target Return
- Lets users adjust constraints:
  - Minimum weight per stock
  - Maximum weight per stock
  - Target return (for target-return objective)
- Lets users adjust risk preference via a risk-tolerance slider
- Displays efficient frontier and selected portfolio point

## Setup
1. Install dependencies:
   - `pip install -r requirements.txt`
2. Run the app:
   - `streamlit run app.py`

## Key Method Choices
- Expected returns: historical average daily returns annualized by 252 trading days
- Risk model: annualized covariance matrix of historical returns
- Optimizer: SLSQP constrained optimization from `scipy.optimize.minimize`

## Limitations
- Historical returns may not predict future performance.
- Market regimes change, so estimates can drift.
- Tight constraints can produce infeasible optimization settings.
