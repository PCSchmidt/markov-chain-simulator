import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import numpy as np
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
import json
from typing import List
from .markov_chain import run_markov_simulation  # Make sure this import is correct

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the directory of the current file (main.py)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level to the project root and then into the static folder
static_dir = os.path.join(current_dir, "..", "static")

# Mount the static files directory
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.on_event("startup")
async def startup_event():
    FastAPICache.init(InMemoryBackend())

@app.get("/")
async def root():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/fetch-data/{symbol}")
@cache(expire=3600)  # Cache for 1 hour
async def get_stock_data(symbol: str, period: str = Query("1y", regex="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$")):
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period)
        
        if data.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}. The stock may be delisted or the symbol may be incorrect.")
        
        # Convert Timestamp index to string dates
        stock_data = data['Close'].to_dict()
        stock_data = {k.strftime("%Y-%m-%d"): float(v) if np.isfinite(v) else None for k, v in stock_data.items()}
        
        return {"symbol": symbol, "data": stock_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data for {symbol}: {str(e)}")

@app.get("/simulate/{symbol}")
async def simulate(
    symbol: str,
    n_simulations: int = Query(1000, ge=1, le=10000),
    n_steps: int = Query(30, ge=1, le=252),
    n_states: int = Query(3, ge=2, le=10),
    discretization_method: str = Query("equal_freq", regex="^(equal_width|equal_freq)$")
):
    try:
        stock_data = await get_stock_data(symbol, "1y")
        prices = list(stock_data['data'].values())
        
        simulated_prices, transition_matrix = run_markov_simulation(prices, n_simulations, n_steps, n_states, discretization_method)
        
        result = {
            "simulated_prices": simulated_prices,
            "transition_matrix": transition_matrix,
            "parameters": {
                "n_simulations": n_simulations,
                "n_steps": n_steps,
                "n_states": n_states,
                "discretization_method": discretization_method
            }
        }
        return JSONResponse(content=json.loads(json.dumps(result, default=float)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error simulating {symbol}: {str(e)}")

# Add other route handlers here (like simulate, etc.)
