# Building the Capstone with the DRIVER Framework

This capstone was built using an iterative DRIVER workflow to integrate valuation + portfolio optimization + a third analytical module into one end-to-end system.

## 1. Define (`/driver:define`)
- **Problem:** Standalone valuation and standalone optimization do not show how assumption changes propagate across a full investment workflow.
- **Solution:** Build one integrated application where valuation outputs feed portfolio construction and users can observe downstream effects.
- **Capstone Requirements Mapped:**
  - Adjustable valuation inputs
  - Adjustable optimization inputs
  - Integrated data flow between components
  - Cross-component sensitivity demonstration
  - One additional student-designed component

## 2. Represent (Architecture & Data Flow)
Pipeline architecture:
1. Input ticker universe
2. Per-ticker DCF valuation
3. Undervaluation screening
4. Additional module adjusts expected returns using momentum and volatility regime penalties
5. Portfolio optimization under constraints
6. Scenario rerun for ripple analysis

## 3. Implement
- Implemented integrated Streamlit app in `capstone_app.py`.
- Reused core methods from both prior projects:
  - DCF valuation mechanics from Project 1
  - SLSQP optimization mechanics from Project 2
- Added new adjustable component:
  - valuation signal weight
  - momentum signal weight
  - momentum window
  - volatility penalty weight

## 4. Validate
Validation checks included:
- Input constraints (5-15 tickers, min weight <= max weight)
- Error handling for missing fundamentals and price history
- Optimization infeasibility handling via custom exception
- Cross-component sanity check by rerunning pipeline under shifted WACC

## 5. Evolve (`/driver:evolve`)
System evolved from two separate project apps into one pipeline that:
- traces assumptions from valuation to optimizer outputs,
- makes integration visible with intermediate tables,
- includes side-by-side scenario outputs for stronger explanation quality.

## 6. Reflect (`/driver:reflect`)
- **What worked:** modular pipeline design made integration explainable for presentation.
- **Tradeoffs:** DCF and historical-return estimates can both be unstable in stressed markets.
- **Professional use case:** practical screening and scenario-analysis assistant, not a fully automated investment decision engine.
- **AI disclosure:** AI was used for coding acceleration, debugging support, and documentation drafting; project framing and financial interpretation remained student-led.
