import yfinance as yf
import pandas as pd
import numpy as np
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_financial_data(df):
    """Clean financial data by replacing inf, -inf, and NaN with None, and handling extreme values."""
    logger.info(f"Raw data sample:\n{df.head().to_string()}")
    logger.info(f"Data types: {df.dtypes}")
    logger.info(f"Any NaN values: {df.isna().any().to_dict()}")
    logger.info(f"Any infinite values: {np.isinf(df).any().to_dict()}")

    def clean_value(x):
        if pd.isna(x) or np.isinf(x) or not np.isfinite(x):
            return None
        return x

    cleaned = df.map(clean_value)  # Use .map() instead of .applymap()
    logger.info(f"Cleaned data sample:\n{cleaned.head().to_string()}")
    return cleaned

def fetch_stock_data(symbol: str, period: str = "1y") -> dict:
    """
    Fetch historical stock data for a given symbol.
    
    :param symbol: Stock symbol (e.g., 'AAPL' for Apple)
    :param period: Time period to fetch data for (default is 1 year)
    :return: DataFrame containing dates and closing prices
    """
    try:
        logger.info(f"Fetching data for {symbol} over {period}")
        stock = yf.Ticker(symbol)
        
        # Try different periods if '1y' doesn't work
        periods = ['1y', '6mo', '3mo', '1mo']
        data = pd.DataFrame()
        for p in periods:
            data = stock.history(period=p)
            if not data.empty:
                break
        
        if data.empty:
            raise ValueError(f"No data available for {symbol}")

        logger.info(f"Successfully fetched {len(data)} days of data for {symbol}")
        
        # Clean the data
        cleaned_data = clean_financial_data(data)
        
        # Remove any rows with None values in the 'Close' column
        cleaned_data = cleaned_data.dropna(subset=['Close'])
        
        result = {
            "price": cleaned_data["Close"].tolist(),
            "dates": cleaned_data.index.strftime('%Y-%m-%d').tolist(),
            "volume": cleaned_data["Volume"].tolist()
        }
        
        logger.info(f"Processed data for {symbol}: {len(result['price'])} price points, {len(result['dates'])} dates, {len(result['volume'])} volume points")
        logger.info(f"Sample of processed data: {result['price'][:5]}")
        
        return result
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        raise ValueError(f"Error fetching data for {symbol}: {str(e)}")

def process_data_for_markov(data: pd.DataFrame) -> pd.Series:
    """
    Process the fetched data for use in the Markov Chain model.
    
    :param data: DataFrame with 'date' and 'price' columns
    :return: Series of prices indexed by date
    """
    return data['price']

# Example usage
if __name__ == "__main__":
    symbol = "AAPL"
    raw_data = fetch_stock_data(symbol)
    processed_data = process_data_for_markov(raw_data)
    print(f"Fetched {len(processed_data)} days of data for {symbol}")
    print(processed_data.head())