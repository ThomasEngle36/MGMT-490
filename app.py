import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="Corporate Valuation Application", layout="wide")

st.title("Corporate Valuation Application (DCF Model)")
st.markdown("""
This application allows you to perform a simple Discounted Cash Flow (DCF) valuation on any publicly traded company. 
It utilizes **yfinance** to pull live financial data, projects future free cash flows, and visualizes how sensitive the valuation is to WACC and Terminal Growth Rate.
""")

st.sidebar.header("Valuation Inputs")

ticker_input = st.sidebar.text_input("Ticker Symbol (e.g., AAPL, MSFT)", value="AAPL")

# Dynamic Sliders
wacc = st.sidebar.slider("WACC (Cost of Capital) %", min_value=1.0, max_value=25.0, value=10.0, step=0.1) / 100.0
st_growth_rate = st.sidebar.slider("Short-Term Growth Rate (Next 5 Years) %", min_value=-10.0, max_value=50.0, value=6.0, step=0.5) / 100.0
term_growth_rate = st.sidebar.slider("Terminal Growth Rate %", min_value=0.5, max_value=5.0, value=2.5, step=0.1) / 100.0

@st.cache_data(ttl=3600)
def fetch_financial_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        
        # Get base info
        info = ticker.info
        current_price = info.get("currentPrice", info.get("regularMarketPrice", 0))
        shares_out = info.get("sharesOutstanding", 0)
        
        if shares_out == 0 or current_price == 0:
            return None, "Incomplete basic data (shares or price missing)."
            
        # Get financials
        cashflow = ticker.cashflow
        balance_sheet = ticker.balance_sheet
        
        # Need latest Operating Cash Flow and CapEx
        # Usually 'Operating Cash Flow' and 'Capital Expenditure'
        if cashflow is not None and not cashflow.empty:
            if 'Operating Cash Flow' in cashflow.index:
                ocf = cashflow.loc['Operating Cash Flow'].iloc[0]
            else:
                return None, "Operating Cash Flow data not available."
                
            if 'Capital Expenditure' in cashflow.index:
                capex = cashflow.loc['Capital Expenditure'].iloc[0]
                # Sometimes CapEx is reported as negative, we want the absolute magnitude to subtract
                if capex < 0:
                    capex = abs(capex)
            else:
                return None, "Capital Expenditure data not available."
        else:
             return None, "Cashflow statement not available."

        # Calculate base FCF
        fcf_base = ocf - capex

        # Get Debt and Cash
        if balance_sheet is not None and not balance_sheet.empty:
            total_debt = 0
            if 'Total Debt' in balance_sheet.index:
                total_debt = balance_sheet.loc['Total Debt'].iloc[0]
            
            total_cash = 0
            if 'Cash And Cash Equivalents' in balance_sheet.index:
                total_cash += balance_sheet.loc['Cash And Cash Equivalents'].iloc[0]
            if 'Other Short Term Investments' in balance_sheet.index:
                # Add short term investments if available
                short_term_inv = balance_sheet.loc['Other Short Term Investments'].iloc[0]
                if not pd.isna(short_term_inv):
                    total_cash += short_term_inv
        else:
             return None, "Balance sheet not available."
             
        # Catch negative FCF edge case for base year gracefully
        if pd.isna(fcf_base):
             return None, "Could not calculate Free Cash Flow."

        data = {
            "current_price": current_price,
            "shares_outstanding": shares_out,
            "ocf": ocf,
            "capex": capex,
            "fcf_base": fcf_base,
            "total_debt": total_debt,
            "total_cash": total_cash
        }
        return data, None
        
    except Exception as e:
        return None, str(e)


def run_dcf(fcf_base, wacc, st_growth, term_growth, total_cash, total_debt, shares_out):
    # Projections for 5 years
    years = 5
    projected_fcfs = []
    current_fcf = fcf_base
    
    # Calculate present value of FCFs
    pv_fcfs = 0
    for i in range(1, years + 1):
        current_fcf = current_fcf * (1 + st_growth)
        projected_fcfs.append(current_fcf)
        discount_factor = (1 + wacc) ** i
        pv_fcfs += current_fcf / discount_factor
        
    # Calculate Terminal Value (Gordon Growth Model)
    # TV = FCF_5 * (1 + g) / (WACC - g)
    terminal_fcf = projected_fcfs[-1] * (1 + term_growth)
    
    if wacc <= term_growth:
        # Invalid math fallback
        terminal_value = 0
    else:
        terminal_value = terminal_fcf / (wacc - term_growth)
        
    # Discount TV to PV
    pv_tv = terminal_value / ((1 + wacc) ** years)
    
    # Enterprise Value
    enterprise_value = pv_fcfs + pv_tv
    
    # Equity Value = Enterprise Value + Cash - Debt
    equity_value = enterprise_value + total_cash - total_debt
    
    # Per Share Value
    per_share_value = equity_value / shares_out if shares_out > 0 else 0
    
    return enterprise_value, equity_value, per_share_value, projected_fcfs, terminal_value

if ticker_input:
    st.write(f"### Fetching data for {ticker_input}...")
    data, error = fetch_financial_data(ticker_input)
    
    if error:
        st.error(f"Error fetching data for {ticker_input}: {error}")
    elif data:
        st.success("Data successfully loaded!")
        
        # Base Data Display
        col1, col2, col3 = st.columns(3)
        col1.metric("Current Stock Price", f"${data['current_price']:,.2f}")
        col2.metric("Shares Outstanding", f"{data['shares_outstanding']:,.0f}")
        col3.metric("Base Year FCF", f"${data['fcf_base']:,.0f}")
        
        # Run base DCF
        ev, eq, share_val, _, _ = run_dcf(
            data['fcf_base'], wacc, st_growth_rate, term_growth_rate, 
            data['total_cash'], data['total_debt'], data['shares_outstanding']
        )
        
        st.write("---")
        st.header("Valuation Outputs")
        
        val_col1, val_col2, val_col3 = st.columns(3)
        
        val_col1.metric("Enterprise Value", f"${ev:,.0f}")
        val_col2.metric("Equity Value", f"${eq:,.0f}")
        
        # Delta color based on current price
        delta = share_val - data['current_price']
        val_col3.metric("Implied Per-Share Value", f"${share_val:,.2f}", f"{delta:,.2f} vs current", delta_color="normal")
        
        st.write("---")
        st.header("Sensitivity Analysis")
        st.markdown("Exploring how **Per-Share Value** changes across different WACC and Terminal Growth Rate assumptions.")
        
        # Generate Sensitivity Table (WACC vs Term Growth)
        wacc_range = np.linspace(max(0.01, wacc - 0.05), wacc + 0.05, 7) # +/- 5% spread
        term_g_range = np.linspace(max(0.0, term_growth_rate - 0.015), term_growth_rate + 0.015, 7) # +/- 1.5% spread
        
        # We need WACC on X axis, Term G on Y axis
        sensitivity_matrix = np.zeros((len(term_g_range), len(wacc_range)))
        
        for i, g in enumerate(term_g_range):
            for j, w in enumerate(wacc_range):
                _, _, val, _, _ = run_dcf(
                     data['fcf_base'], w, st_growth_rate, g, 
                     data['total_cash'], data['total_debt'], data['shares_outstanding']
                )
                sensitivity_matrix[i, j] = val
                
        # Create DataFrame for Seaborn
        df_sens = pd.DataFrame(
            sensitivity_matrix, 
            index=[f"{g*100:.1f}%" for g in term_g_range],
            columns=[f"{w*100:.1f}%" for w in wacc_range]
        )
        
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(df_sens, annot=True, fmt=".2f", cmap="RdYlGn", center=data['current_price'], ax=ax, cbar_kws={'label': 'Implied Share Price'})
        ax.set_xlabel("WACC (Cost of Capital)")
        ax.set_ylabel("Terminal Growth Rate")
        ax.set_title("Sensitivity of Per-Share Value")
        
        st.pyplot(fig)
        
        # Stability / Edge Cases Reminder
        st.info("Remember to test edge cases in your demo (e.g., negative FCF bases, very high WACCs). If Base FCF is negative, the DCF relies heavily on future growth turnaround or results in negative value.")
