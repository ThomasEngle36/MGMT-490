import numpy as np
import pandas as pd

TRADING_DAYS = 252


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
    ret = portfolio_return(weights, expected_returns)
    return float((ret - risk_free_rate) / vol)
