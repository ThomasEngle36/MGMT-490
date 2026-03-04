# Building with the DRIVER Framework

This project was developed adhering to the **DRIVER** methodology, utilizing the **FAskills Plugin** and **Gemini AI** as collaborative coding assistants. DRIVER is an iterative, structured approach to building software applications that ensures each phase—from conceptualization to final reflection—is clearly defined and executable. 

By utilizing these collaborative AI tools while following this framework, the DCF Generator project maintained a tight scope, robust testing, and clear documentation. Below is an outline of how each phase of the framework was applied to this specific tool:


## 1. Define (`/driver:define`)
*   **The Problem:** Traditional Excel-based DCF models are manual, prone to data-entry errors, and time-consuming to update when market conditions change.
*   **The Solution:** An automated web application that programmatically fetches financial data and dynamically runs intrinsic valuations.
*   **Key Requirements:** 
    *   Dynamic data fetching via financial APIs (`yfinance`).
    *   Flexibility to alter assumptions (WACC, Growth Rates).
    *   A user-friendly UI to instantly display valuations.

## 2. Represent (Architecture & Logic)
*   **Data Models:** Outlined the required inputs from the income statement, balance sheet, and cash flow statement (e.g., Operating Cash Flow, Capex, Total Debt, Cash & Equivalents, Shares Outstanding).
*   **Mathematical Models:** Formally defined the Python implementation for the core DCF equations, including the accurate projection of 5-year Free Cash Flows and the calculation of the Perpetuity Terminal Value.
*   **UI Layout:** Sketched the structure of the Streamlit dashboard to ensure outputs like Enterprise Value, Equity Value, and the Per-Share Implied Value were displayed clearly alongside sensitivity metrics.

## 3. Implement (Coding the Engine & UI)
*   **Backend Engine:** Developed the core Python logic to ingest current ticker data, map financial metrics to the DCF formulas, and handle edge cases (e.g., negative base free cash flows or missing API data).
*   **Frontend Integration:** Integrated the engine with Streamlit to create an interactive, responsive web application where users can input dynamic sliders for short-term growth and discount rates.

## 4. Validate (Stress-Testing)
*   **Accuracy Checks:** Tested the application using real-world public companies, specifically focusing on a base case scenario for a mature company like Walmart ($WMT). 
*   **Sanity Checks:** Verified that the core equations structurally matched traditional financial models, ensuring that an increase in the discount rate accurately decreased the implied stock price, and vice versa.

## 5. Evolve (`/driver:evolve`)
*   **Expanding Functionality:** Based on the successful base model, the project was expanded to include a sophisticated 2D Sensitivity Analysis heatmap. 
*   **Deeper Insights:** This evolution moved the tool from a simple static calculator into a dynamic environment where users can simultaneously test various Terminal Growth Rates against different WACC scenarios.

## 6. Reflect (`/driver:reflect`)
*   **Presentation:** Authored a comprehensive video script tailored to presenting the DCF methodology, defending WACC assumptions, and explaining the sensitivity outputs.
*   **Publishing:** Drafted a cohesive Substack post to introduce the tool's mechanics and the value of automating intrinsic valuations.
*   **Transparency:** Clearly documented the role of AI coding assistants throughout the development process, adhering to modern software and academic disclosure standards.
