from typing import Dict, List

import numpy as np
import pandas as pd

from metrics import portfolio_return, portfolio_volatility
from optimizer import OptimizationError, optimize_target_return


def generate_efficient_frontier(
    expected_returns: pd.Series,
    covariance: pd.DataFrame,
    min_weight: float,
    max_weight: float,
    points: int = 40,
) -> pd.DataFrame:
    min_target = float(expected_returns.min())
    max_target = float(expected_returns.max())
    targets = np.linspace(min_target, max_target, points)

    rows: List[Dict] = []
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


def build_weight_table(tickers, weights: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame({"Ticker": list(tickers), "Weight": weights}).sort_values("Weight", ascending=False)


def build_summary(result: Dict) -> Dict:
    return {
        "Expected Annual Return": result["expected_return"],
        "Expected Annual Volatility": result["expected_volatility"],
        "Sharpe Ratio": result["sharpe"],
    }
