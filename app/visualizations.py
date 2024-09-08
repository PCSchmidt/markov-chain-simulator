import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import List, Dict
from memory_profiler import profile

def clean_data(data):
    """Clean data by replacing inf and NaN with None."""
    if isinstance(data, (list, np.ndarray)):
        return [None if not np.isfinite(x) else x for x in data]
    elif isinstance(data, dict):
        return {k: clean_data(v) for k, v in data.items()}
    else:
        return None if not np.isfinite(data) else data

def plot_price_history(prices: pd.Series) -> dict:
    """Create an interactive candlestick chart for price history."""
    try:
        df = prices.resample('D').ohlc()
        
        fig = go.Figure(data=[go.Candlestick(x=df.index,
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'])])
        
        fig.update_layout(title='Price History',
                          xaxis_title='Date',
                          yaxis_title='Price',
                          xaxis_rangeslider_visible=False)
        
        plot_data = fig.to_dict()
        
        # Convert numpy arrays and datetime objects to serializable format
        for trace in plot_data['data']:
            for key, value in trace.items():
                if isinstance(value, np.ndarray):
                    trace[key] = clean_data(value.tolist())
                elif isinstance(value, pd.DatetimeIndex):
                    trace[key] = value.strftime('%Y-%m-%d').tolist()
        
        return clean_data(plot_data)
    except Exception as e:
        return {'error': str(e)}

def plot_returns_distribution(returns: pd.Series) -> dict:
    """Create an interactive histogram for returns distribution."""
    try:
        fig = px.histogram(returns, nbins=50, title='Returns Distribution')
        fig.update_layout(xaxis_title='Returns', yaxis_title='Frequency')
        
        plot_data = fig.to_dict()
        
        # Convert numpy arrays to lists and clean data
        for trace in plot_data['data']:
            for key, value in trace.items():
                if isinstance(value, np.ndarray):
                    trace[key] = clean_data(value.tolist())
        
        return clean_data(plot_data)
    except Exception as e:
        return {'error': str(e)}

@profile
def plot_transition_matrix(transition_matrix: np.ndarray) -> dict:
    """Create a heatmap visualization of the transition matrix."""
    fig = px.imshow(transition_matrix,
                    labels=dict(x="To State", y="From State", color="Probability"),
                    x=[f'State {i}' for i in range(transition_matrix.shape[1])],
                    y=[f'State {i}' for i in range(transition_matrix.shape[0])],
                    title='Transition Matrix')
    
    fig.update_xaxes(side="top")
    
    return fig.to_dict()

def plot_simulations(simulations: List[List[int]], initial_price: float, returns: pd.Series) -> dict:
    """Create a line plot of multiple price simulations."""
    n_simulations = len(simulations)
    n_steps = len(simulations[0])
    
    # Convert states to prices
    state_returns = returns.groupby(pd.qcut(returns, q=max(max(sim) for sim in simulations) + 1, labels=False)).mean()
    simulated_prices = np.array([[initial_price * np.exp(np.sum(state_returns.iloc[states[:i]])) for i in range(n_steps)] for states in simulations])
    
    fig = go.Figure()
    
    for i in range(n_simulations):
        fig.add_trace(go.Scatter(y=simulated_prices[i], mode='lines', name=f'Simulation {i+1}'))
    
    fig.update_layout(title='Price Simulations',
                      xaxis_title='Time Steps',
                      yaxis_title='Price',
                      showlegend=False)
    
    return fig.to_dict()

def prepare_price_history_data(prices: pd.Series) -> dict:
    """Prepare price history data for frontend visualization."""
    df = prices.resample('D').ohlc()
    return {
        'dates': df.index.strftime('%Y-%m-%d').tolist(),
        'open': df['open'].tolist(),
        'high': df['high'].tolist(),
        'low': df['low'].tolist(),
        'close': df['close'].tolist()
    }

def prepare_returns_distribution_data(returns: pd.Series) -> dict:
    """Prepare returns distribution data for frontend visualization."""
    return {
        'returns': returns.tolist()
    }
