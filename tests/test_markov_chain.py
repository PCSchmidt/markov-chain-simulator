import pytest
import pandas as pd
import numpy as np
from app.markov_chain import calculate_returns, discretize_returns_equal_freq, create_transition_matrix, run_markov_simulation

def test_calculate_returns():
    prices = pd.Series([100, 110, 105, 115, 120])
    expected_returns = np.log(prices / prices.shift(1)).dropna()
    calculated_returns = calculate_returns(prices)
    assert np.allclose(calculated_returns, expected_returns)

def test_discretize_returns_equal_freq():
    returns = pd.Series([-0.02, -0.01, 0, 0.01, 0.02])
    discretized = discretize_returns_equal_freq(returns, 3)
    assert len(discretized) == 5
    assert discretized.nunique() == 3

def test_create_transition_matrix():
    discretized_returns = np.array([0, 1, 2, 1, 0, 1])
    n_states = 3
    transition_matrix = create_transition_matrix(discretized_returns, n_states)
    assert transition_matrix.shape == (3, 3)
    assert np.allclose(transition_matrix.sum(axis=1), 1)

def test_run_markov_simulation():
    returns = pd.Series(np.random.normal(0, 0.01, 100))
    simulations, transition_matrix = run_markov_simulation(returns, n_simulations=10, n_steps=20, n_states=3)
    assert len(simulations) == 10
    assert len(simulations[0]) == 20
    assert transition_matrix.shape == (3, 3)

# Add more tests as needed
