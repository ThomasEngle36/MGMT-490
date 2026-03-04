# Corporate Valuation Application (MGMT 490)

## Project Description
This is a Streamlit application designed for performing Discounted Cash Flow (DCF) valuations dynamically using real-time financial data. It allows analysts to stress-test their assumptions including Cost of Capital (WACC), Short-Term Growth Rates, and Terminal Growth Rates.

## Project Goals
- **Automate Valuation Mechanics:** Eliminate the repetitive data-gathering and calculation processes inherent to traditional Excel DCF models.
- **Dynamic Stress-Testing:** Provide an interactive tool (via a 2D Heatmap) for stress-testing intrinsic valuations under various economic scenarios.
- **Apply Financial Theory in Code:** Demonstrate proficiency in building robust financial applications using Python, Streamlit, and modern structured development frameworks.

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

## Data Sources
This application pulls all fundamental financial data dynamically using the open-source `yfinance` library. **No private API keys are required or included in this repository.** Anyone can clone this project, install the requirements, and run the application out of the box using public Yahoo Finance data.

## AI Usage Disclosure and Reflection
This project was built with the assistance of AI tools, specifically Google DeepMind's Gemini and the FAskills DRIVER AI framework plugin.
- **Usage:** Specifically, AI was utilized to help structure the base Python logic, troubleshoot data manipulation utilizing `pandas` and `streamlit`, and format the frontend user interface. 
- **Reflection:** The core financial modeling theory, the selection of the DCF methodology, and the fundamental assumptions utilized during the valuation analysis (such as projecting WMT's WACC and Growth rate) were guided entirely by my own analytical research. Utilizing AI significantly reduced the friction of translating financial concepts into working code, allowing me to focus more deeply on the actual valuation mechanics and sensitivity outcomes rather than getting bogged down by syntax errors.

## Author
Prepared for MGMT 490 Corporate Valuation Project.
