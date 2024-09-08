import numpy as np
import pandas as pd
from scipy import stats
from typing import Tuple, List, Callable

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

def run_markov_simulation(returns: pd.Series, n_simulations: int = 1000, n_steps: int = 30, n_states: int = 3, discretization_method: str = "equal_freq") -> Tuple[List[np.ndarray], np.ndarray]:
    """
    Run Markov Chain Monte Carlo simulation.
    
    Args:
        returns (pd.Series): Series of historical returns
        n_simulations (int): Number of simulations to run
        n_steps (int): Number of steps in each simulation
        n_states (int): Number of states for discretization
        discretization_method (str): Method for discretizing returns ('equal_freq' or 'equal_width')
    
    Returns:
        Tuple[List[np.ndarray], np.ndarray]: List of simulations and transition matrix
    """
    if discretization_method == "equal_freq":
        discretized_returns = discretize_returns_equal_freq(returns, n_states)
    elif discretization_method == "equal_width":
        discretized_returns = discretize_returns_equal_width(returns, n_states)
    else:
        raise ValueError("Invalid discretization method. Use 'equal_freq' or 'equal_width'.")

    # Convert to numeric codes
    if isinstance(discretized_returns, pd.Categorical):
        discretized_returns = discretized_returns.codes
    elif isinstance(discretized_returns, pd.Series) and isinstance(discretized_returns.dtype, pd.CategoricalDtype):
        discretized_returns = discretized_returns.cat.codes
    else:
        discretized_returns = pd.factorize(discretized_returns)[0]

    transition_matrix = create_transition_matrix(discretized_returns, n_states)
    
    initial_state = discretized_returns[-1]
    simulations = [simulate_markov_chain(initial_state, transition_matrix, n_steps) 
                   for _ in range(n_simulations)]
    
    return simulations, transition_matrix

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
