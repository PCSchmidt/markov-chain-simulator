import logging
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, constr
from typing import Dict, List
import pandas as pd
import numpy as np
from .data_fetcher import fetch_stock_data
from .risk_analysis import perform_risk_analysis
from .visualizations import prepare_price_history_data, prepare_returns_distribution_data, plot_transition_matrix
from .markov_chain import run_markov_simulation, compare_models, calculate_returns, simulate_prices
import asyncio
import json
import traceback
from whitenoise import WhiteNoise
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Access environment variables
API_KEY = os.getenv("API_KEY")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Wrap your app with WhiteNoise
app = WhiteNoise(app, root="static/")

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

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/fetch-data/{symbol}", response_model=StockData)
async def get_stock_data(symbol: constr(min_length=1, max_length=10), period: str = Query("1y", regex="^[1-5][ydwm]$")) -> StockData:
    try:
        data = fetch_stock_data(symbol, period)
        if not data['price']:  # Check if the list is empty
            raise ValueError(f"No data available for {symbol}")
        # Convert data to the format expected by the frontend
        data_dict = {str(i): price for i, price in enumerate(data['price'])}
        return StockData(symbol=symbol, data=data_dict)
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Error fetching data for {symbol}: {str(e)}")

@app.get("/risk-analysis/{symbol}", response_model=RiskAnalysis)
async def get_risk_analysis(symbol: constr(min_length=1, max_length=10), period: str = Query("1y", regex="^[1-5][ydwm]$")) -> RiskAnalysis:
    try:
        data = fetch_stock_data(symbol, period)
        risk_metrics = perform_risk_analysis(data['price'])
        return RiskAnalysis(**risk_metrics)
    except ValueError as e:
        logger.error(f"Error performing risk analysis for {symbol}: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Error performing risk analysis for {symbol}: {str(e)}")

@app.get("/visualize/{symbol}")
async def get_visualizations(
    symbol: constr(min_length=1, max_length=10),
    period: str = Query("1y", regex="^[1-5][ydwm]$")
):
    try:
        logger.info(f"Fetching data for {symbol}")
        data = fetch_stock_data(symbol, period)
        
        logger.info(f"Preparing price history for {symbol}")
        price_history = {
            'dates': data['dates'],
            'prices': data['price']
        }
        
        logger.info(f"Calculating returns for {symbol}")
        returns = calculate_returns(data['price'])
        
        result = {
            "price_history": price_history,
            "returns_distribution": returns
        }

        logger.info(f"Visualization data prepared for {symbol}")
        logger.info(f"Sample of price data: {result['price_history']['prices'][:5]}")
        logger.info(f"Sample of returns data: {result['returns_distribution'][:5]}")
        
        json_result = json.dumps(result, default=custom_json_serializer)
        logger.info(f"JSON encoding successful for {symbol}")
        
        return JSONResponse(content=json.loads(json_result))
    except Exception as e:
        logger.error(f"Error in get_visualizations for {symbol}: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/simulate/{symbol}")
async def run_simulation(
    symbol: constr(min_length=1, max_length=10),
    n_simulations: int = Query(1000, ge=1, le=10000),
    n_steps: int = Query(30, ge=1, le=252),
    n_states: int = Query(3, ge=2, le=10),
    discretization_method: str = Query("equal_freq", regex="^(equal_width|equal_freq)$")
):
    try:
        data = fetch_stock_data(symbol, "1y")
        if not data['price'] or len(data['price']) < 2:
            raise ValueError(f"Insufficient data for {symbol}")
        
        returns = calculate_returns(pd.Series(data['price']))
        initial_price = data['price'][-1]

        simulations, transition_matrix = run_markov_simulation(
            returns, n_simulations, n_steps, n_states, discretization_method
        )

        simulated_prices = [simulate_prices(initial_price, sim, returns).tolist() for sim in simulations[:10]]  # Limit to 10 simulations for visualization

        result = {
            "simulated_prices": simulated_prices,
            "transition_matrix": transition_matrix.tolist(),
            "transition_matrix_plot": plot_transition_matrix(transition_matrix),
            "parameters": {
                "n_simulations": n_simulations,
                "n_steps": n_steps,
                "n_states": n_states,
                "discretization_method": discretization_method
            }
        }

        logger.info(f"Simulation result structure: {json.dumps(result, default=custom_json_serializer)}")

        return JSONResponse(content=json.loads(json.dumps(result, default=custom_json_serializer)))
    except Exception as e:
        logger.error(f"Error in run_simulation for {symbol}: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(content={"error": str(e)}, status_code=500)

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