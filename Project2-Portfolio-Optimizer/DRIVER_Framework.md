# Building with the DRIVER Framework

This project was developed using the **DRIVER** methodology with AI-assisted coding support. DRIVER provides a structured path from problem definition through implementation, testing, iteration, and reflection. For this project, the framework was applied to build a portfolio optimization tool that is stable, explainable, and aligned to the MGMT 490 grading rubric.

Below is how each DRIVER phase was applied to the Portfolio Optimizer (Project 2):

## 1. Define (`/driver:define`)
- **The Problem:** Investors need a practical way to compare portfolios under different risk tolerances and constraints. A single "optimal" answer is not sufficient for real decision-making.
- **The Solution:** A Streamlit application that accepts multiple stock tickers, estimates return/risk from historical data, and computes optimized allocations under user-defined constraints.
- **Key Requirements:**
  - Accept 5-15 tickers.
  - Retrieve market data dynamically (`yfinance`).
  - Compute expected returns, covariance, and portfolio-level risk/return.
  - Support multiple objectives (Max Sharpe, Min Variance, Target Return).
  - Allow constraint/risk adjustments and show the efficient frontier.

## 2. Represent (Architecture & Logic)
- **Data Model:** Ticker list -> historical prices -> return series -> annualized expected returns and covariance matrix.
- **Optimization Model:** Constrained nonlinear optimization using `scipy.optimize.minimize` (SLSQP) with:
  - Sum of weights = 1,
  - Per-asset min/max bounds,
  - Optional target-return inequality constraint.
- **UI Model:** Sidebar controls for tickers, history window, objective, min/max weights, risk tolerance, and optional target return. Main panel for KPI outputs, weight table/chart, and efficient frontier.

## 3. Implement (Coding the Engine & UI)
- **Backend Modules:**
  - `data.py`: ticker parsing/validation, Yahoo price retrieval, return computation.
  - `metrics.py`: annualized statistics and portfolio metrics.
  - `optimizer.py`: objective functions and constrained solver logic.
  - `frontier.py`: efficient frontier construction and output formatting.
- **Frontend Integration (`app.py`):**
  - Input validation and error messaging,
  - Objective selection and risk-tolerance control,
  - Display of optimized weights and return/risk KPIs,
  - Plotly visualizations for allocation and efficient frontier.

## 4. Validate (Testing & Sanity Checks)
- **Functional Checks:**
  - Verified ticker count constraints (min 5 / max 15),
  - Verified infeasible settings are handled with readable errors,
  - Verified outputs update when objective and constraints are changed.
- **Numerical Checks:**
  - Ensured weights sum to approximately 1,
  - Ensured weights remain within selected bounds,
  - Confirmed expected risk-return tradeoff behavior on the frontier.

## 5. Evolve (`/driver:evolve`)
- **Incremental Improvements Added:**
  - Risk-tolerance slider blending conservative and aggressive allocations,
  - Efficient frontier with selected-portfolio marker and equal-weight baseline,
  - Expanded diagnostics section for expected returns and covariance transparency.
- **Scalability Path:**
  - Future upgrades could include transaction costs, short-selling toggle, Black-Litterman return estimates, and backtesting.

## 6. Reflect (`/driver:reflect`)
- **What Worked:** Separating the app into modular files made debugging and explanation much easier.
- **Tradeoffs Acknowledged:** Historical-average return estimates are intuitive but sensitive to window selection and market regime changes.
- **AI Usage Transparency:** AI assistance was used for implementation acceleration, error handling structure, and documentation clarity. The optimization objective choices, financial interpretation, and project framing were guided by course requirements and independent judgment.

---

Prepared for **MGMT 490 - Project 2 (Investment Management Application, Path A: Portfolio Optimizer)**.
