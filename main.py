import configparser
import yfinance as yf
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plot
import mplfinance as mpf
import plotly.graph_objects as graph
import datetime
import tkinter as tk
from tkinter import messagebox

## Importing your Config ##

def load_config():
    config = configparser.ConfigParser()
    config.read("config.ini")
    risk_free_rate = float(config["DEFAULT"].get("risk_free_rate", 0.05)) # Default Value 5%  
    historical_data_period = config["DEFAULT"].get("historical_data_period", "1y") # Default Time-Frame 1yr
    return risk_free_rate, historical_data_period
  
## Data Retrieval Function ##

def retrieve(symbol, historical_data_period):
    try:
        ticker = yf.Ticker(symbol)
        current_price = ticker.history(period="1d")['Close'].iloc[-1]
        historical_data = ticker.history(period=historical_data_period)

        # Volatility
        returns = np.log(historical_data['Close'] / historical_data['Close'].shift(1)).dropna() # dropna() should avoid NaN errors or ZeroDivision
        volatility = np.std(returns) * np.sqrt(252)  # 252 are the average trading days in the US
        
        # Options Chain Retrieval
        option_dates = ticker.options
        if option_dates:
            data = ticker.option_chain(option_dates[0])
            return current_price, volatility, data.calls, data.puts
        else:
            print(f"No option found for ticker {symbol}.")
            return current_price, volatility, None, None
    except Exception as e:
        print(f"Error in data retrieving for {symbol}: {e}")
        return None, None, None, None

## Main ##

def main():
  symbol = input("Insert ticker (e.g. AAPL, TSLA): ").upper()
  calls, puts = retrieve(symbol)
    
