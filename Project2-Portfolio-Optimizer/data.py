import re
from typing import List, Tuple

import numpy as np
import pandas as pd
import yfinance as yf


def parse_tickers(raw: str) -> List[str]:
    tokens = re.split(r"[\s,;]+", raw.strip().upper())
    deduped: List[str] = []
    seen = set()
    for token in tokens:
        if token and token not in seen:
            deduped.append(token)
            seen.add(token)
    return deduped


def validate_tickers(tickers: List[str], min_count: int = 5, max_count: int = 15) -> Tuple[bool, str]:
    if len(tickers) < min_count:
        return False, f"Please enter at least {min_count} unique tickers."
    if len(tickers) > max_count:
        return False, f"Please enter at most {max_count} unique tickers."
    return True, ""


def _extract_close_prices(raw_prices: pd.DataFrame) -> pd.DataFrame:
    if raw_prices.empty:
        return pd.DataFrame()

    if isinstance(raw_prices.columns, pd.MultiIndex):
        level0 = raw_prices.columns.get_level_values(0)
        if "Adj Close" in level0:
            return raw_prices["Adj Close"].copy()
        if "Close" in level0:
            return raw_prices["Close"].copy()
        return pd.DataFrame()

    for col in ["Adj Close", "Close"]:
        if col in raw_prices.columns:
            single = raw_prices[[col]].copy()
            single.columns = ["SINGLE"]
            return single

    return pd.DataFrame()


def download_prices(tickers: List[str], period: str = "3y", interval: str = "1d") -> pd.DataFrame:
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

    prices = _extract_close_prices(raw)
    if prices.empty:
        return pd.DataFrame()

    if isinstance(prices, pd.Series):
        prices = prices.to_frame()

    min_non_null = max(int(0.7 * len(prices.index)), 2)
    prices = prices.dropna(axis=1, thresh=min_non_null)
    prices = prices.dropna(axis=0, how="any")
    return prices


def compute_returns(prices: pd.DataFrame, method: str = "pct") -> pd.DataFrame:
    if prices.empty:
        return pd.DataFrame()

    if method == "log":
        ratio = prices / prices.shift(1)
        ratio = ratio.where(ratio > 0)
        return np.log(ratio).dropna()

    return prices.pct_change().dropna()
