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

def retrieve(symbol):
  ticker = yf.ticker(symbol)
  option_date = ticker.options
  data = options.data(option_date[0])
  if option_date:
        data = ticker.option_chain(option_date[0])  oni
        return data.calls, data.puts
  else:
        print("No option found for ticker {symbol}")
        return None, None

## Main ##

def main():
  symbol = input("Insert ticker (e.g. AAPL, TSLA): ").upper()
  calls, puts = retrieve(symbol)
    
