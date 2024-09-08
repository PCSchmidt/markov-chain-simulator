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

# Create a WhiteNoise object for serving static files
whitenoise = WhiteNoise(app, root="static/")

class StockData(BaseModel):
    symbol: constr(min_length=1, max_length=10)
    data: Dict[str, float]

class RiskAnalysis(BaseModel):
    volatility: float
    var_95: float
    cvar_95: float
    sharpe_ratio: float
    max_drawdown: float

class MarkovSimulation(BaseModel):
    simulations: List[List[int]]
    transition_matrix: List[List[float]]

class ModelComparison(BaseModel):
    n_states: int
    mean: float
    std: float
    skew: float
    kurtosis: float
    transition_matrix: List[List[float]]

@app.on_event("shutdown")
async def shutdown_event():
    # Cancel all running tasks
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Close any open connections or resources here
    # For example, if you're using a database:
    # await database.disconnect()

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


@app.get("/compare-models/{symbol}")
async def compare_markov_models(
    symbol: constr(min_length=1, max_length=10),
    n_states_list: str = Query("2,3,4,5", regex="^[0-9,]+$"),
    n_simulations: int = Query(1000, ge=1, le=10000),
    n_steps: int = Query(30, ge=1, le=252)
):
    try:
        data = fetch_stock_data(symbol, "1y")
        if not data['price'] or len(data['price']) < 2:
            raise ValueError(f"Insufficient data for {symbol}")
        
        returns = calculate_returns(pd.Series(data['price']))
        n_states_list = [int(n) for n in n_states_list.split(',')]
        
        comparison_results = compare_models(returns, n_states_list, n_simulations, n_steps)
        
        return JSONResponse(content=json.loads(json.dumps(comparison_results, default=custom_json_serializer)))
    except Exception as e:
        logger.error(f"Error in compare_markov_models for {symbol}: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(content={"error": str(e)}, status_code=500)

# TODO: Add more endpoints for visualization and historical comparison

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred. Please try again later."}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

def calculate_returns(prices):
    prices_series = pd.Series(prices)
    returns = prices_series.pct_change().dropna()
    return returns.tolist()

def custom_json_serializer(obj):
    if isinstance(obj, (np.int64, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

# At the end of the file, expose the WhiteNoise wrapped app
app = whitenoise

# Add other route handlers here (like simulate, etc.)

