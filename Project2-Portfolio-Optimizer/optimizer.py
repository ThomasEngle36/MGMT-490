from typing import Dict, Optional

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from metrics import portfolio_return, portfolio_volatility, sharpe_ratio


class OptimizationError(Exception):
    pass


def _base_constraints(expected_returns: pd.Series, min_weight: float, max_weight: float):
    n_assets = len(expected_returns)
    bounds = tuple((min_weight, max_weight) for _ in range(n_assets))
    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    return n_assets, bounds, constraints


def _solve(objective_fn, n_assets, bounds, constraints):
    x0 = np.array([1.0 / n_assets] * n_assets)
    result = minimize(objective_fn, x0=x0, method="SLSQP", bounds=bounds, constraints=constraints)
    if not result.success:
        raise OptimizationError(result.message)
    return result.x


def optimize_min_variance(
    expected_returns: pd.Series,
    covariance: pd.DataFrame,
    min_weight: float = 0.0,
    max_weight: float = 1.0,
) -> np.ndarray:
    n_assets, bounds, constraints = _base_constraints(expected_returns, min_weight, max_weight)
    return _solve(lambda w: portfolio_volatility(w, covariance), n_assets, bounds, constraints)


def optimize_max_sharpe(
    expected_returns: pd.Series,
    covariance: pd.DataFrame,
    risk_free_rate: float = 0.02,
    min_weight: float = 0.0,
    max_weight: float = 1.0,
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
    min_weight: float = 0.0,
    max_weight: float = 1.0,
) -> np.ndarray:
    n_assets, bounds, constraints = _base_constraints(expected_returns, min_weight, max_weight)
    constraints = constraints + [
        {"type": "ineq", "fun": lambda w: portfolio_return(w, expected_returns) - target_return}
    ]
    return _solve(lambda w: portfolio_volatility(w, covariance), n_assets, bounds, constraints)


def optimize_portfolio(
    expected_returns: pd.Series,
    covariance: pd.DataFrame,
    objective: str,
    risk_free_rate: float = 0.02,
    min_weight: float = 0.0,
    max_weight: float = 1.0,
    target_return: Optional[float] = None,
) -> Dict:
    objective_key = objective.strip().lower()

    if objective_key == "max sharpe":
        weights = optimize_max_sharpe(expected_returns, covariance, risk_free_rate, min_weight, max_weight)
    elif objective_key == "min variance":
        weights = optimize_min_variance(expected_returns, covariance, min_weight, max_weight)
    elif objective_key == "target return":
        if target_return is None:
            raise OptimizationError("Target return objective selected but target return is missing.")
        weights = optimize_target_return(
            expected_returns,
            covariance,
            target_return,
            min_weight,
            max_weight,
        )
    else:
        raise OptimizationError(f"Unsupported objective: {objective}")

    return {
        "weights": weights,
        "expected_return": portfolio_return(weights, expected_returns),
        "expected_volatility": portfolio_volatility(weights, covariance),
        "sharpe": sharpe_ratio(weights, expected_returns, covariance, risk_free_rate),
    }


def blend_weights(low_risk_weights: np.ndarray, high_risk_weights: np.ndarray, risk_tolerance: float) -> np.ndarray:
    alpha = min(max(risk_tolerance, 0.0), 1.0)
    mixed = (1.0 - alpha) * low_risk_weights + alpha * high_risk_weights
    return mixed / mixed.sum()
