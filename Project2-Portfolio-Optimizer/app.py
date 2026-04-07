import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data import compute_returns, download_prices, parse_tickers, validate_tickers
from frontier import build_summary, build_weight_table, generate_efficient_frontier
from metrics import annualized_covariance, annualized_expected_returns, portfolio_return, portfolio_volatility, sharpe_ratio
from optimizer import OptimizationError, blend_weights, optimize_max_sharpe, optimize_min_variance, optimize_portfolio

st.set_page_config(page_title="Portfolio Optimizer", layout="wide")
st.title("Portfolio Optimizer (Path A)")
st.caption("Adjust constraints and risk preferences to analyze optimal portfolio changes.")

with st.sidebar:
    st.header("Portfolio Inputs")
    tickers_raw = st.text_area(
        "Tickers (comma/newline separated, 5-15)",
        value="AAPL, MSFT, NVDA, AMZN, GOOGL, JPM",
        height=110,
    )
    period = st.selectbox("History period", ["1y", "2y", "3y", "5y"], index=2)
    interval = st.selectbox("Data interval", ["1d", "1wk", "1mo"], index=0)
    risk_free_rate = st.number_input("Risk-free rate", min_value=0.0, max_value=0.2, value=0.02, step=0.005)

    st.subheader("Constraints")
    min_weight = st.slider("Min weight per stock", min_value=0.0, max_value=0.3, value=0.0, step=0.01)
    max_weight = st.slider("Max weight per stock", min_value=0.1, max_value=1.0, value=0.35, step=0.01)

    st.subheader("Objective and Risk")
    objective = st.selectbox("Objective", ["Max Sharpe", "Min Variance", "Target Return"])
    risk_tolerance = st.slider(
        "Risk tolerance (0=Conservative, 1=Aggressive)",
        min_value=0.0,
        max_value=1.0,
        value=0.6,
        step=0.05,
    )

    target_return = None
    if objective == "Target Return":
        target_return = st.number_input("Target annual return", min_value=-0.2, max_value=1.0, value=0.15, step=0.01)

run = st.button("Run Optimization", type="primary")

if min_weight > max_weight:
    st.error("Min weight cannot be greater than max weight.")
    st.stop()

if run:
    tickers = parse_tickers(tickers_raw)
    valid, message = validate_tickers(tickers)
    if not valid:
        st.error(message)
        st.stop()

    try:
        with st.spinner("Retrieving historical price data..."):
            prices = download_prices(tickers=tickers, period=period, interval=interval)

        if prices.empty or prices.shape[1] < 2:
            st.error("Not enough valid historical data. Try different tickers or a longer period.")
            st.stop()

        kept_tickers = list(prices.columns)
        dropped_tickers = [t for t in tickers if t not in kept_tickers]
        if dropped_tickers:
            st.warning(f"Dropped tickers due to missing data: {', '.join(dropped_tickers)}")

        returns = compute_returns(prices, method="pct")
        if returns.empty:
            st.error("Return series is empty after preprocessing.")
            st.stop()

        expected_returns = annualized_expected_returns(returns)
        covariance = annualized_covariance(returns)

        base = optimize_portfolio(
            expected_returns=expected_returns,
            covariance=covariance,
            objective=objective,
            risk_free_rate=risk_free_rate,
            min_weight=min_weight,
            max_weight=max_weight,
            target_return=target_return,
        )

        min_var_w = optimize_min_variance(expected_returns, covariance, min_weight, max_weight)
        max_sharpe_w = optimize_max_sharpe(expected_returns, covariance, risk_free_rate, min_weight, max_weight)
        blended_w = blend_weights(min_var_w, max_sharpe_w, risk_tolerance)

        final_weights = base["weights"] if objective == "Target Return" else blended_w
        final_result = {
            "weights": final_weights,
            "expected_return": portfolio_return(final_weights, expected_returns),
            "expected_volatility": portfolio_volatility(final_weights, covariance),
            "sharpe": sharpe_ratio(final_weights, expected_returns, covariance, risk_free_rate),
        }

        summary = build_summary(final_result)
        weights_df = build_weight_table(kept_tickers, final_result["weights"])

        c1, c2, c3 = st.columns(3)
        c1.metric("Expected Annual Return", f"{summary['Expected Annual Return']:.2%}")
        c2.metric("Expected Annual Volatility", f"{summary['Expected Annual Volatility']:.2%}")
        c3.metric("Sharpe Ratio", f"{summary['Sharpe Ratio']:.3f}")

        st.subheader("Optimal Weights")
        st.dataframe(weights_df, use_container_width=True)
        st.plotly_chart(px.bar(weights_df, x="Ticker", y="Weight", title="Optimal Allocation"), use_container_width=True)

        st.subheader("Efficient Frontier")
        frontier = generate_efficient_frontier(expected_returns, covariance, min_weight=min_weight, max_weight=max_weight, points=40)
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
                x=[final_result["expected_volatility"]],
                y=[final_result["expected_return"]],
                mode="markers",
                marker={"size": 12},
                name="Selected Portfolio",
            )
        )

        eq_weights = np.array([1.0 / len(kept_tickers)] * len(kept_tickers))
        fig.add_trace(
            go.Scatter(
                x=[portfolio_volatility(eq_weights, covariance)],
                y=[portfolio_return(eq_weights, expected_returns)],
                mode="markers",
                marker={"size": 10},
                name="Equal Weight Baseline",
            )
        )

        fig.update_layout(
            xaxis_title="Annualized Volatility",
            yaxis_title="Annualized Return",
            template="plotly_white",
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Expected returns and covariance details"):
            st.write("Annualized expected returns")
            st.dataframe(expected_returns.to_frame("Expected Return"), use_container_width=True)
            st.write("Annualized covariance matrix")
            st.dataframe(covariance, use_container_width=True)

    except OptimizationError as err:
        st.error(f"Optimization failed: {err}")
    except Exception as err:
        st.error(f"Unexpected error: {err}")
else:
    st.info("Set your inputs in the sidebar and click Run Optimization.")
