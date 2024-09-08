import numpy as np
import pandas as pd
from memory_profiler import profile

def calculate_returns(prices):
    """Calculate daily returns from a series of prices."""
    return np.log(prices / prices.shift(1)).dropna()

def calculate_volatility(returns, window=30):
    """Calculate rolling volatility of returns."""
    return returns.rolling(window=window).std() * np.sqrt(252)

def calculate_var(returns, confidence_level=0.95):
    """Calculate Value at Risk (VaR) for a given confidence level."""
    return np.percentile(returns, (1 - confidence_level) * 100)

def calculate_cvar(returns, confidence_level=0.95):
    """Calculate Conditional Value at Risk (CVaR) for a given confidence level."""
    var = calculate_var(returns, confidence_level)
    return returns[returns <= var].mean()

@profile
def perform_risk_analysis(prices):
    """Perform basic risk analysis on a series of prices."""
    returns = calculate_returns(prices)
    volatility = calculate_volatility(returns)
    var_95 = calculate_var(returns)
    cvar_95 = calculate_cvar(returns)
    
    return {
        "volatility": volatility.iloc[-1],
        "var_95": var_95,
        "cvar_95": cvar_95,
        "sharpe_ratio": (returns.mean() * 252) / (returns.std() * np.sqrt(252)),
        "max_drawdown": (prices / prices.cummax() - 1).min()
    }
