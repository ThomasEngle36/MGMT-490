from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from scipy.optimize import minimize

TRADING_DAYS = 252

st.set_page_config(page_title="Integrated Finance Capstone", layout="wide")
st.title("Integrated Finance Capstone: Valuation -> Screening -> Portfolio")
st.caption(
    "Pipeline: DCF valuation (Project 1) feeds a screened universe into portfolio optimization "
    "(Project 2), with an added momentum/regime module to adjust expected returns."
)


class OptimizationError(Exception):
    pass


def parse_tickers(raw: str) -> List[str]:
    tokens = raw.upper().replace("\n", ",").replace(";", ",").split(",")
    deduped: List[str] = []
    seen = set()
    for token in tokens:
        cleaned = token.strip()
        if cleaned and cleaned not in seen:
            deduped.append(cleaned)
            seen.add(cleaned)
    return deduped


@st.cache_data(ttl=3600)
def fetch_financial_data(ticker_symbol: str) -> Tuple[Optional[Dict], Optional[str]]:
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        current_price = info.get("currentPrice", info.get("regularMarketPrice", 0))
        shares_out = info.get("sharesOutstanding", 0)

        if not current_price or not shares_out:
            return None, "Missing current price or shares outstanding."

        cashflow = ticker.cashflow
        balance_sheet = ticker.balance_sheet
        if cashflow is None or cashflow.empty:
            return None, "Cash flow statement unavailable."
        if balance_sheet is None or balance_sheet.empty:
            return None, "Balance sheet unavailable."

        if "Operating Cash Flow" not in cashflow.index:
            return None, "Operating Cash Flow unavailable."
        if "Capital Expenditure" not in cashflow.index:
            return None, "Capital Expenditure unavailable."

        ocf = cashflow.loc["Operating Cash Flow"].iloc[0]
        capex = cashflow.loc["Capital Expenditure"].iloc[0]
        capex = abs(capex) if capex < 0 else capex
        fcf_base = ocf - capex
        if pd.isna(fcf_base):
            return None, "Could not calculate base free cash flow."

        total_debt = (
            balance_sheet.loc["Total Debt"].iloc[0] if "Total Debt" in balance_sheet.index else 0.0
        )
        total_cash = 0.0
        if "Cash And Cash Equivalents" in balance_sheet.index:
            total_cash += float(balance_sheet.loc["Cash And Cash Equivalents"].iloc[0])
        if "Other Short Term Investments" in balance_sheet.index:
            short_term_inv = balance_sheet.loc["Other Short Term Investments"].iloc[0]
            if not pd.isna(short_term_inv):
                total_cash += float(short_term_inv)

        return {
            "ticker": ticker_symbol,
            "current_price": float(current_price),
            "shares_outstanding": float(shares_out),
            "fcf_base": float(fcf_base),
            "total_debt": float(total_debt),
            "total_cash": float(total_cash),
        }, None
    except Exception as err:
        return None, str(err)


def run_dcf(
    fcf_base: float,
    wacc: float,
    st_growth: float,
    term_growth: float,
    total_cash: float,
    total_debt: float,
    shares_out: float,
) -> Dict:
    years = 5
    projected_fcfs: List[float] = []
    pv_fcfs = 0.0
    current_fcf = float(fcf_base)
    for year in range(1, years + 1):
        current_fcf = current_fcf * (1 + st_growth)
        projected_fcfs.append(current_fcf)
        pv_fcfs += current_fcf / ((1 + wacc) ** year)

    terminal_fcf = projected_fcfs[-1] * (1 + term_growth)
    terminal_value = 0.0 if wacc <= term_growth else terminal_fcf / (wacc - term_growth)
    pv_terminal = terminal_value / ((1 + wacc) ** years)

    enterprise_value = pv_fcfs + pv_terminal
    equity_value = enterprise_value + total_cash - total_debt
    implied_per_share = equity_value / shares_out if shares_out > 0 else 0.0

    return {
        "enterprise_value": float(enterprise_value),
        "equity_value": float(equity_value),
        "implied_per_share": float(implied_per_share),
        "terminal_value": float(terminal_value),
    }


@st.cache_data(ttl=3600)
def download_prices(tickers: List[str], period: str, interval: str) -> pd.DataFrame:
    if not tickers:
        return pd.DataFrame()
    raw = yf.download(
        tickers=tickers,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
        group_by="column",
        threads=True,
    )
    if raw.empty:
        return pd.DataFrame()
    if isinstance(raw.columns, pd.MultiIndex):
        if "Adj Close" in raw.columns.get_level_values(0):
            prices = raw["Adj Close"].copy()
        elif "Close" in raw.columns.get_level_values(0):
            prices = raw["Close"].copy()
        else:
            return pd.DataFrame()
    else:
        col = "Adj Close" if "Adj Close" in raw.columns else "Close"
        if col not in raw.columns:
            return pd.DataFrame()
        prices = raw[[col]].copy()
        prices.columns = tickers[:1]

    if isinstance(prices, pd.Series):
        prices = prices.to_frame()
    min_non_null = max(int(0.7 * len(prices.index)), 2)
    prices = prices.dropna(axis=1, thresh=min_non_null).dropna(axis=0, how="any")
    return prices


def annualized_expected_returns(returns: pd.DataFrame) -> pd.Series:
    return returns.mean() * TRADING_DAYS


def annualized_covariance(returns: pd.DataFrame) -> pd.DataFrame:
    return returns.cov() * TRADING_DAYS


def portfolio_return(weights: np.ndarray, expected_returns: pd.Series) -> float:
    return float(np.dot(weights, expected_returns.values))


def portfolio_volatility(weights: np.ndarray, covariance: pd.DataFrame) -> float:
    return float(np.sqrt(weights.T @ covariance.values @ weights))


def sharpe_ratio(
    weights: np.ndarray,
    expected_returns: pd.Series,
    covariance: pd.DataFrame,
    risk_free_rate: float,
) -> float:
    vol = portfolio_volatility(weights, covariance)
    if vol <= 1e-12:
        return float("-inf")
    return (portfolio_return(weights, expected_returns) - risk_free_rate) / vol


def _base_constraints(expected_returns: pd.Series, min_weight: float, max_weight: float):
    n_assets = len(expected_returns)
    bounds = tuple((min_weight, max_weight) for _ in range(n_assets))
    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    return n_assets, bounds, constraints


def _solve(objective_fn, n_assets: int, bounds, constraints) -> np.ndarray:
    x0 = np.array([1.0 / n_assets] * n_assets)
    result = minimize(objective_fn, x0=x0, method="SLSQP", bounds=bounds, constraints=constraints)
    if not result.success:
        raise OptimizationError(result.message)
    return result.x


def optimize_min_variance(
    expected_returns: pd.Series,
    covariance: pd.DataFrame,
    min_weight: float,
    max_weight: float,
) -> np.ndarray:
    n_assets, bounds, constraints = _base_constraints(expected_returns, min_weight, max_weight)
    return _solve(lambda w: portfolio_volatility(w, covariance), n_assets, bounds, constraints)


def optimize_max_sharpe(
    expected_returns: pd.Series,
    covariance: pd.DataFrame,
    risk_free_rate: float,
    min_weight: float,
    max_weight: float,
) -> np.ndarray:
    n_assets, bounds, constraints = _base_constraints(expected_returns, min_weight, max_weight)
    return _solve(
        lambda w: -sharpe_ratio(w, expected_returns, covariance, risk_free_rate),
        n_assets,
        bounds,
        constraints,
    )


def optimize_target_return(
    expected_returns: pd.Series,
    covariance: pd.DataFrame,
    target_return: float,
    min_weight: float,
    max_weight: float,
) -> np.ndarray:
    n_assets, bounds, constraints = _base_constraints(expected_returns, min_weight, max_weight)
    constraints = constraints + [
        {"type": "ineq", "fun": lambda w: portfolio_return(w, expected_returns) - target_return}
    ]
    return _solve(lambda w: portfolio_volatility(w, covariance), n_assets, bounds, constraints)


def generate_efficient_frontier(
    expected_returns: pd.Series,
    covariance: pd.DataFrame,
    min_weight: float,
    max_weight: float,
    points: int = 40,
) -> pd.DataFrame:
    targets = np.linspace(float(expected_returns.min()), float(expected_returns.max()), points)
    rows = []
    for target in targets:
        try:
            weights = optimize_target_return(
                expected_returns=expected_returns,
                covariance=covariance,
                target_return=float(target),
                min_weight=min_weight,
                max_weight=max_weight,
            )
            rows.append(
                {
                    "target_return": float(target),
                    "return": portfolio_return(weights, expected_returns),
                    "volatility": portfolio_volatility(weights, covariance),
                }
            )
        except OptimizationError:
            continue
    return pd.DataFrame(rows)


def run_pipeline(
    tickers: List[str],
    wacc: float,
    st_growth_rate: float,
    term_growth_rate: float,
    undervaluation_threshold: float,
    valuation_weight: float,
    momentum_weight: float,
    momentum_window: int,
    volatility_penalty: float,
    period: str,
    interval: str,
    risk_free_rate: float,
    objective: str,
    min_weight: float,
    max_weight: float,
    target_return: Optional[float],
) -> Dict:
    valuation_rows = []
    for ticker in tickers:
        base, err = fetch_financial_data(ticker)
        if err or not base:
            valuation_rows.append({"Ticker": ticker, "error": err or "Unknown valuation error."})
            continue

        dcf = run_dcf(
            fcf_base=base["fcf_base"],
            wacc=wacc,
            st_growth=st_growth_rate,
            term_growth=term_growth_rate,
            total_cash=base["total_cash"],
            total_debt=base["total_debt"],
            shares_out=base["shares_outstanding"],
        )
        mispricing_pct = ((dcf["implied_per_share"] - base["current_price"]) / base["current_price"]) * 100.0
        valuation_rows.append(
            {
                "Ticker": ticker,
                "Current Price": base["current_price"],
                "Implied Price": dcf["implied_per_share"],
                "Mispricing %": mispricing_pct,
                "Pass Valuation Screen": mispricing_pct >= undervaluation_threshold,
                "error": None,
            }
        )

    valuation_df = pd.DataFrame(valuation_rows)
    if valuation_df.empty:
        raise ValueError("No valuation results were produced.")

    screened_df = valuation_df[
        (valuation_df["error"].isna()) & (valuation_df["Pass Valuation Screen"])
    ].copy()
    screened_tickers = screened_df["Ticker"].tolist()

    if len(screened_tickers) < 2:
        raise ValueError(
            "Fewer than 2 stocks passed valuation screen. Lower undervaluation threshold or expand ticker list."
        )

    prices = download_prices(screened_tickers, period=period, interval=interval)
    if prices.empty or prices.shape[1] < 2:
        raise ValueError("Not enough valid historical price data for screened stocks.")

    kept_tickers = list(prices.columns)
    returns = prices.pct_change().dropna()
    if returns.empty:
        raise ValueError("Return series is empty after preprocessing.")

    expected_returns_hist = annualized_expected_returns(returns)
    covariance = annualized_covariance(returns)
    momentum_signal = prices.pct_change(momentum_window).iloc[-1] * (TRADING_DAYS / momentum_window)
    volatility_signal = returns.std() * np.sqrt(TRADING_DAYS)

    mispricing_series = (
        screened_df.set_index("Ticker")["Mispricing %"].reindex(kept_tickers).fillna(0.0) / 100.0
    )
    adjusted_expected_returns = (
        expected_returns_hist
        + valuation_weight * mispricing_series
        + momentum_weight * momentum_signal.reindex(kept_tickers).fillna(0.0)
        - volatility_penalty * volatility_signal.reindex(kept_tickers).fillna(0.0)
    )

    if min_weight > max_weight:
        raise ValueError("Min weight cannot exceed max weight.")

    objective_key = objective.strip().lower()
    if objective_key == "max sharpe":
        weights = optimize_max_sharpe(
            expected_returns=adjusted_expected_returns,
            covariance=covariance,
            risk_free_rate=risk_free_rate,
            min_weight=min_weight,
            max_weight=max_weight,
        )
    elif objective_key == "min variance":
        weights = optimize_min_variance(adjusted_expected_returns, covariance, min_weight, max_weight)
    elif objective_key == "target return":
        if target_return is None:
            raise ValueError("Target return objective selected but target return is missing.")
        weights = optimize_target_return(
            expected_returns=adjusted_expected_returns,
            covariance=covariance,
            target_return=target_return,
            min_weight=min_weight,
            max_weight=max_weight,
        )
    else:
        raise ValueError(f"Unsupported objective: {objective}")

    portfolio = {
        "weights": weights,
        "expected_return": portfolio_return(weights, adjusted_expected_returns),
        "expected_volatility": portfolio_volatility(weights, covariance),
        "sharpe": sharpe_ratio(weights, adjusted_expected_returns, covariance, risk_free_rate),
    }

    diag = pd.DataFrame(
        {
            "Ticker": kept_tickers,
            "Expected Return (Historical)": expected_returns_hist.reindex(kept_tickers).values,
            "Mispricing Signal": mispricing_series.reindex(kept_tickers).values,
            "Momentum Signal": momentum_signal.reindex(kept_tickers).fillna(0.0).values,
            "Volatility Penalty Signal": volatility_signal.reindex(kept_tickers).fillna(0.0).values,
            "Expected Return (Adjusted)": adjusted_expected_returns.reindex(kept_tickers).values,
        }
    )

    frontier = generate_efficient_frontier(
        expected_returns=adjusted_expected_returns,
        covariance=covariance,
        min_weight=min_weight,
        max_weight=max_weight,
        points=40,
    )

    weights_df = (
        pd.DataFrame({"Ticker": kept_tickers, "Weight": weights})
        .sort_values("Weight", ascending=False)
        .reset_index(drop=True)
    )

    return {
        "valuation_df": valuation_df.drop(columns=["error"], errors="ignore"),
        "screened_df": screened_df,
        "diagnostic_df": diag,
        "weights_df": weights_df,
        "frontier_df": frontier,
        "portfolio": portfolio,
    }


with st.sidebar:
    st.header("Universe + Valuation Inputs")
    tickers_raw = st.text_area(
        "Tickers (comma/newline separated, 5-15)",
        value="AAPL, MSFT, NVDA, AMZN, GOOGL, JPM, WMT, XOM",
        height=110,
    )
    wacc = st.slider("WACC %", min_value=1.0, max_value=25.0, value=10.0, step=0.1) / 100.0
    st_growth_rate = (
        st.slider("Short-Term Growth % (5 years)", min_value=-10.0, max_value=50.0, value=6.0, step=0.5) / 100.0
    )
    term_growth_rate = st.slider("Terminal Growth %", min_value=0.5, max_value=5.0, value=2.5, step=0.1) / 100.0
    undervaluation_threshold = st.slider(
        "Valuation Screen: Min undervaluation %",
        min_value=-20.0,
        max_value=50.0,
        value=10.0,
        step=1.0,
    )

    st.header("Additional Component: Return Adjustment")
    valuation_weight = st.slider("Valuation signal weight", min_value=0.0, max_value=1.0, value=0.35, step=0.05)
    momentum_weight = st.slider("Momentum signal weight", min_value=0.0, max_value=1.0, value=0.20, step=0.05)
    momentum_window = st.slider("Momentum window (trading days)", min_value=20, max_value=252, value=63, step=5)
    volatility_penalty = st.slider("Volatility penalty weight", min_value=0.0, max_value=1.0, value=0.10, step=0.05)

    st.header("Portfolio Optimization Inputs")
    period = st.selectbox("History period", ["1y", "2y", "3y", "5y"], index=2)
    interval = st.selectbox("Data interval", ["1d", "1wk", "1mo"], index=0)
    risk_free_rate = st.number_input("Risk-free rate", min_value=0.0, max_value=0.2, value=0.02, step=0.005)
    min_weight = st.slider("Min weight per stock", min_value=0.0, max_value=0.3, value=0.0, step=0.01)
    max_weight = st.slider("Max weight per stock", min_value=0.1, max_value=1.0, value=0.35, step=0.01)
    objective = st.selectbox("Objective", ["Max Sharpe", "Min Variance", "Target Return"])
    target_return = None
    if objective == "Target Return":
        target_return = st.number_input("Target annual return", min_value=-0.2, max_value=1.0, value=0.15, step=0.01)

    st.header("Cross-Component Sensitivity Demo")
    enable_ripple = st.checkbox("Run automatic ripple comparison", value=True)
    ripple_wacc_shift_bps = st.slider("Scenario WACC shift (bps)", min_value=-300, max_value=300, value=100, step=25)

run = st.button("Run Integrated Pipeline", type="primary")

if not run:
    st.info("Set your assumptions and click Run Integrated Pipeline.")
    st.stop()

tickers = parse_tickers(tickers_raw)
if len(tickers) < 5 or len(tickers) > 15:
    st.error("Please enter between 5 and 15 unique tickers.")
    st.stop()

try:
    with st.spinner("Running valuation, screening, and optimization..."):
        base_result = run_pipeline(
            tickers=tickers,
            wacc=wacc,
            st_growth_rate=st_growth_rate,
            term_growth_rate=term_growth_rate,
            undervaluation_threshold=undervaluation_threshold,
            valuation_weight=valuation_weight,
            momentum_weight=momentum_weight,
            momentum_window=momentum_window,
            volatility_penalty=volatility_penalty,
            period=period,
            interval=interval,
            risk_free_rate=risk_free_rate,
            objective=objective,
            min_weight=min_weight,
            max_weight=max_weight,
            target_return=target_return,
        )

    st.success("Pipeline completed.")
    p = base_result["portfolio"]
    k1, k2, k3 = st.columns(3)
    k1.metric("Expected Annual Return", f"{p['expected_return']:.2%}")
    k2.metric("Expected Annual Volatility", f"{p['expected_volatility']:.2%}")
    k3.metric("Sharpe Ratio", f"{p['sharpe']:.3f}")

    st.subheader("Step 1: DCF Valuation for Universe")
    st.dataframe(
        base_result["valuation_df"][
            ["Ticker", "Current Price", "Implied Price", "Mispricing %", "Pass Valuation Screen"]
        ],
        use_container_width=True,
    )

    st.subheader("Step 2: Valuation Screen Output")
    screened = base_result["screened_df"]
    if screened.empty:
        st.warning("No stocks passed the valuation screen.")
    else:
        st.write(f"{len(screened)} stocks passed: {', '.join(screened['Ticker'].tolist())}")
        st.dataframe(screened[["Ticker", "Mispricing %"]], use_container_width=True)

    st.subheader("Step 3: Additional Module + Optimizer Inputs")
    st.caption(
        "Historical expected return is adjusted by valuation mispricing, momentum, and volatility penalty "
        "before optimization."
    )
    st.dataframe(base_result["diagnostic_df"], use_container_width=True)

    st.subheader("Step 4: Optimized Portfolio")
    weights_df = base_result["weights_df"]
    st.dataframe(weights_df, use_container_width=True)
    st.plotly_chart(px.bar(weights_df, x="Ticker", y="Weight", title="Optimal Allocation"), use_container_width=True)

    st.subheader("Efficient Frontier")
    frontier = base_result["frontier_df"]
    fig = go.Figure()
    if not frontier.empty:
        fig.add_trace(
            go.Scatter(
                x=frontier["volatility"],
                y=frontier["return"],
                mode="lines",
                name="Efficient Frontier",
            )
        )
    fig.add_trace(
        go.Scatter(
            x=[p["expected_volatility"]],
            y=[p["expected_return"]],
            mode="markers",
            marker={"size": 12},
            name="Selected Portfolio",
        )
    )
    fig.update_layout(
        xaxis_title="Annualized Volatility",
        yaxis_title="Annualized Return",
        template="plotly_white",
    )
    st.plotly_chart(fig, use_container_width=True)

    if enable_ripple:
        shifted_wacc = max(0.01, wacc + ripple_wacc_shift_bps / 10000.0)
        with st.spinner("Running scenario for cross-component sensitivity..."):
            scenario_result = run_pipeline(
                tickers=tickers,
                wacc=shifted_wacc,
                st_growth_rate=st_growth_rate,
                term_growth_rate=term_growth_rate,
                undervaluation_threshold=undervaluation_threshold,
                valuation_weight=valuation_weight,
                momentum_weight=momentum_weight,
                momentum_window=momentum_window,
                volatility_penalty=volatility_penalty,
                period=period,
                interval=interval,
                risk_free_rate=risk_free_rate,
                objective=objective,
                min_weight=min_weight,
                max_weight=max_weight,
                target_return=target_return,
            )

        st.subheader("Cross-Component Sensitivity (Ripple View)")
        st.write(
            f"Base WACC: {wacc:.2%} | Scenario WACC: {shifted_wacc:.2%}. "
            "This changes valuation outputs, then screening outcomes, then final portfolio weights."
        )

        base_pass = set(base_result["screened_df"]["Ticker"].tolist())
        scenario_pass = set(scenario_result["screened_df"]["Ticker"].tolist())
        delta_rows = [
            {"Metric": "Screened Stocks Count", "Base": len(base_pass), "Scenario": len(scenario_pass)},
            {"Metric": "Expected Return", "Base": p["expected_return"], "Scenario": scenario_result["portfolio"]["expected_return"]},
            {"Metric": "Expected Volatility", "Base": p["expected_volatility"], "Scenario": scenario_result["portfolio"]["expected_volatility"]},
            {"Metric": "Sharpe Ratio", "Base": p["sharpe"], "Scenario": scenario_result["portfolio"]["sharpe"]},
        ]
        st.dataframe(pd.DataFrame(delta_rows), use_container_width=True)
        st.write(f"Added by scenario: {', '.join(sorted(scenario_pass - base_pass)) or 'None'}")
        st.write(f"Removed by scenario: {', '.join(sorted(base_pass - scenario_pass)) or 'None'}")

        merged_weights = pd.merge(
            base_result["weights_df"].rename(columns={"Weight": "Base Weight"}),
            scenario_result["weights_df"].rename(columns={"Weight": "Scenario Weight"}),
            on="Ticker",
            how="outer",
        ).fillna(0.0)
        merged_weights["Weight Change"] = merged_weights["Scenario Weight"] - merged_weights["Base Weight"]
        st.dataframe(merged_weights.sort_values("Weight Change", ascending=False), use_container_width=True)

except (OptimizationError, ValueError) as err:
    st.error(f"Pipeline failed: {err}")
except Exception as err:
    st.error(f"Unexpected error: {err}")
