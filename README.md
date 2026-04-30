# Integrated Finance Capstone (MGMT 490)

## Project Overview
This capstone combines:
- **Project 1 (Valuation):** DCF model with adjustable WACC, short-term growth, and terminal growth.
- **Project 2 (Portfolio Optimizer):** constrained portfolio optimization with Max Sharpe, Min Variance, and Target Return objectives.
- **Additional Component (New):** momentum + volatility regime adjustment that modifies expected returns before optimization.

The app is implemented in `capstone_app.py` and demonstrates **cross-component sensitivity** from valuation assumptions to final portfolio allocation.

## Integrated Workflow
1. **Universe Input:** enter 5-15 tickers.
2. **Valuation Engine:** run DCF per ticker and compute implied mispricing.
3. **Valuation Screen:** keep only stocks above a user-defined undervaluation threshold.
4. **Additional Module:** adjust expected returns using valuation signal weight, momentum signal weight, and volatility penalty weight.
5. **Optimization:** optimize the screened universe under user-selected constraints.
6. **Ripple Sensitivity:** optional side-by-side scenario run that shifts WACC and traces impact to screening and final weights.

## Adjustable Inputs
### Valuation Inputs
- WACC
- Short-term growth (5-year)
- Terminal growth
- Minimum undervaluation threshold

### Additional Component Inputs
- Valuation signal weight
- Momentum signal weight
- Momentum window
- Volatility penalty weight

### Portfolio Inputs
- Price history period and interval
- Risk-free rate
- Min/max weight constraints
- Objective (Max Sharpe, Min Variance, Target Return)
- Target return (when applicable)

### Cross-Component Sensitivity Inputs
- Toggle automatic ripple comparison
- Scenario WACC shift (bps)

## Why the Components Connect
- Valuation output (`Mispricing %`) becomes an explicit input to expected return adjustment.
- The adjusted expected returns feed the optimizer objective.
- Changing WACC or growth changes valuation, which changes screen pass/fail, which changes the optimizer universe and final allocations.

## How to Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the integrated app:
   ```bash
   streamlit run capstone_app.py
   ```

## Suggested Demo Flow (Capstone Video)
1. Run base case with 8-10 tickers.
2. Show valuation table and which stocks pass the screen.
3. Show adjusted-return diagnostic table (new component).
4. Show optimized weights and frontier.
5. Turn on ripple comparison and change WACC shift.
6. Explain added/removed tickers and weight changes.

## Limitations
- Yahoo Finance data can have missing/lagged fields.
- DCF is assumption-sensitive, especially terminal value inputs.
- Momentum and volatility adjustments are heuristic and not a full asset-pricing model.
- Errors can compound across stages in a multi-step pipeline.

## AI Usage Disclosure and Reflection
AI tools were used to accelerate implementation, refactoring, and documentation. Financial framing, integration choices, parameter interpretation, and capstone workflow design were directed by the student and project rubric requirements.
