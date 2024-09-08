import numpy as np
import pandas as pd
from scipy import stats
from typing import Tuple, List, Callable
from memory_profiler import profile

def calculate_returns(prices: pd.Series) -> pd.Series:
    """Calculate daily returns from a series of prices."""
    return np.log(prices / prices.shift(1)).dropna()

def discretize_returns_equal_width(returns: pd.Series, n_states: int) -> pd.Series:
    """Discretize returns into states using equal-width bins."""
    return pd.cut(returns, bins=n_states, labels=False)

def discretize_returns_equal_freq(returns: pd.Series, n_states: int) -> pd.Series:
    """Discretize returns into states using equal-frequency bins."""
    return pd.qcut(returns, q=n_states, labels=False)

def discretize_returns_custom(returns: pd.Series, thresholds: List[float]) -> pd.Series:
    """Discretize returns into states using custom thresholds."""
    return pd.cut(returns, bins=[-np.inf] + thresholds + [np.inf], labels=range(len(thresholds) + 1))

def create_transition_matrix(discretized_returns: np.ndarray, n_states: int) -> np.ndarray:
    """Create the transition probability matrix."""
    transitions = np.zeros((n_states, n_states))
    for i in range(len(discretized_returns) - 1):
        from_state, to_state = discretized_returns[i], discretized_returns[i+1]
        transitions[from_state, to_state] += 1
    
    # Normalize to get probabilities
    row_sums = transitions.sum(axis=1)
    transition_matrix = np.divide(transitions, row_sums[:, np.newaxis], where=row_sums[:, np.newaxis]!=0)
    return transition_matrix

def simulate_markov_chain(initial_state: int, transition_matrix: np.ndarray, n_steps: int) -> List[int]:
    """Simulate a Markov chain for a given number of steps."""
    current_state = initial_state
    states = [current_state]
    
    for _ in range(n_steps - 1):
        current_state = np.random.choice(len(transition_matrix), p=transition_matrix[current_state])
        states.append(current_state)
    
    return states

@profile
def run_markov_simulation(prices: List[float], n_simulations: int, n_steps: int, n_states: int, discretization_method: str) -> Tuple[List[List[float]], List[List[float]]]:
    # Calculate returns, removing any infinite or NaN values
    returns = np.diff(prices) / prices[:-1]
    returns = returns[np.isfinite(returns)]
    
    if len(returns) < 2:
        raise ValueError("Not enough valid price data to perform simulation")

    # Discretize returns
    if discretization_method == "equal_width":
        bins = np.linspace(returns.min(), returns.max(), n_states + 1)
    else:  # equal_freq
        bins = np.percentile(returns, np.linspace(0, 100, n_states + 1))
    
    discretized = np.digitize(returns, bins[1:-1])
    
    # Calculate transition matrix
    transition_matrix = np.zeros((n_states, n_states))
    for i in range(len(discretized) - 1):
        transition_matrix[discretized[i], discretized[i+1]] += 1
    
    # Handle potential division by zero
    row_sums = transition_matrix.sum(axis=1, keepdims=True)
    transition_matrix = np.divide(transition_matrix, row_sums, where=row_sums!=0)
    
    # Replace any remaining NaNs with uniform distribution
    nan_rows = np.isnan(transition_matrix).any(axis=1)
    transition_matrix[nan_rows] = 1 / n_states
    
    # Ensure the transition matrix is valid (rows sum to 1)
    transition_matrix /= transition_matrix.sum(axis=1, keepdims=True)
    
    # Simulate
    simulated_prices = []
    initial_price = prices[-1]
    for _ in range(n_simulations):
        current_state = np.random.choice(n_states)
        sim_prices = [initial_price]
        for _ in range(n_steps):
            current_state = np.random.choice(n_states, p=transition_matrix[current_state])
            return_rate = np.random.uniform(bins[current_state], bins[current_state+1])
            sim_prices.append(sim_prices[-1] * (1 + return_rate))
        simulated_prices.append(sim_prices)
    
    return simulated_prices, transition_matrix.tolist()

def simulate_prices(initial_price: float, simulated_states: List[int], returns: pd.Series) -> np.ndarray:
    """Convert simulated states back to prices."""
    returns_series = pd.Series(returns)  # Ensure returns is a pandas Series
    discretized_returns = discretize_returns_equal_freq(returns_series, len(set(simulated_states)))
    state_returns = returns_series.groupby(discretized_returns).mean()
    price_changes = [state_returns.iloc[state] for state in simulated_states]
    return initial_price * np.exp(np.cumsum(price_changes))

def compare_models(returns: pd.Series, n_states_list: List[int], n_simulations: int = 1000, n_steps: int = 30) -> dict:
    """Compare Markov Chain models with different numbers of states."""
    results = {}
    for n_states in n_states_list:
        simulations, transition_matrix = run_markov_simulation(returns, n_simulations, n_steps, n_states)
        simulated_returns = np.diff(np.log(simulate_prices(100, simulations[0], returns)))
        results[n_states] = {
            'mean': np.mean(simulated_returns),
            'std': np.std(simulated_returns),
            'skew': stats.skew(simulated_returns),
            'kurtosis': stats.kurtosis(simulated_returns),
            'transition_matrix': transition_matrix
        }
    return results

# Example usage
if __name__ == "__main__":
    # Sample data (you would typically fetch this from your data_fetcher)
    sample_prices = pd.Series([100, 102, 99, 101, 103, 102, 105, 107, 106, 108], 
                              index=pd.date_range(start="2023-01-01", periods=10))
    
    simulations, transition_matrix = run_markov_simulation(sample_prices)
    print("Transition Matrix:")
    print(transition_matrix)
    
    print("\nSample Simulation (states):")
    print(simulations[0])
    
    print("\nSample Simulation (prices):")
    initial_price = sample_prices.iloc[-1]
    simulated_prices = simulate_prices(initial_price, simulations[0], calculate_returns(sample_prices))
    print(simulated_prices)
