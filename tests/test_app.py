import pytest
from fastapi.testclient import TestClient
from app.main import app  # Import your FastAPI app

client = TestClient(app)

def test_fetch_data():
    response = client.get("/fetch-data/AAPL")
    assert response.status_code == 200
    assert "symbol" in response.json()
    assert "data" in response.json()

def test_simulate_stock():
    response = client.get("/simulate/AAPL?n_simulations=100&n_steps=10&n_states=3&discretization_method=equal_freq")
    assert response.status_code == 200
    assert "symbol" in response.json()
    assert "simulated_data" in response.json()

def test_invalid_stock():
    response = client.get("/fetch-data/INVALID")
    assert response.status_code == 404

# Add more tests as needed
