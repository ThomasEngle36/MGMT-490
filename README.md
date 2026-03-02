# Corporate Valuation Application (MGMT 490)

This is a Streamlit application designed for performing Discounted Cash Flow (DCF) valuations dynamically using real-time financial data. It allows analysts to stress-test their assumptions including Cost of Capital (WACC), Short-Term Growth Rates, and Terminal Growth Rates.

## Features:
1. **Dynamic Data Fetching**: Utilizes `yfinance` to automatically pull Current Stock Price, Shares Outstanding, Operating Cash Flow, Capex, Total Debt, and Cash.
2. **DCF Engine**: Projects 5-year Free Cash Flows and calculates the Terminal Value using the Gordon Growth Model.
3. **Valuation Outputs**: Calculates and explicitly displays Enterprise Value, Equity Value, and an Implied Per-Share Value.
4. **Sensitivity Analysis**: Generates an interactive heatmap demonstrating how implied share prices react to changes in WACC and Terminal Growth Rate assumptions.

## Phase 1 Readiness:
- ✅ Uses `yfinance` to accept a ticker and pull real-time financial data.
- ✅ DCF Engine projecting cash flows.
- ✅ Dynamic inputs for WACC, Short-term Growth Rate, Terminal Growth Rate.
- ✅ Output of Enterprise Value, Equity Value, and Per-Share Value.
- ✅ Interactive 2D Heatmap for Sensitivity Analysis (WACC vs. Term Growth).
- ✅ Built to handle stability (edge-case checks for missing metrics or negative base Free Cash Flows).

## Getting Started

1. Ensure you have Python installed.
2. Clone this repository (or download the files).
3. Install the required dependencies using pip:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```

## Author
Prepared for MGMT 490 Corporate Valuation Project.
