HEAD
# Markov Chain Stock Simulator

This application simulates stock prices using a Markov Chain model and provides comparison functionality for multiple stocks.

## Current Configuration

- Simulation Parameters:
  - Number of simulations: 1000
  - Number of steps: 30
  - Number of states: 3
  - Discretization method: equal frequency

- Stocks data period: 1 year

## How to Run

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/markov-chain-simulator.git
   cd markov-chain-simulator
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the FastAPI server:
   ```
   uvicorn app.main:app --reload
   ```

4. Open your web browser and navigate to `http://localhost:8000`

## Features

- Fetch historical stock data
- Run Markov Chain simulations
- Compare multiple stocks:
  - Historical price comparison
  - Returns distribution comparison
  - Simulated price comparison

## Additional Information

- This project uses FastAPI for the backend and Plotly for data visualization.
- Stock data is fetched using the yfinance library.
- The Markov Chain simulation is implemented using NumPy.

For more detailed information on the implementation, please refer to the source code and comments within the project files.
## License

This project is licensed under the MIT License - see the LICENSE file for details.

# markov-chain-simulator
Takes in ticker symbols and price information and performs a markov chain simulation
0e2880cba1c0525e8bb19648fcb486533aceaaf5


