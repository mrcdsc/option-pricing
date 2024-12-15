import configparser
import yfinance as yf
import numpy as np
import mplfinance as mpf
import datetime
from datetime import datetime
import scipy.stats as si, stats

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
        close_prices = ticker.history(period=historical_data_period)['Close'].tolist() 
        current_price = close_prices[-1]
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

def calculate_time_to_expiration(expiration_date):
    current_date = datetime.now()
    date_delta = expiration_date - current_date
    return date_delta.days / 365.0

## Main ##

class BlackScholesModel:
    def __init__(self, S, K, T, r, sigma):
        self.S = S  # Current Price
        self.K = K  # Strike Price
        self.T = T  # Time to expiration (in yrs)
        self.r = r  # Risk Free Rate
        self.sigma = sigma  # Volatilty

    def d1(self):
        return (np.log(self.S / self.K) + (self.r + 0.5 * self.sigma ** 2) * self.T) / (self.sigma * np.sqrt(self.T))
    
    def d2(self):
        return self.d1() - self.sigma * np.sqrt(self.T)
    
    def call_option_price(self):
        return (self.S * si.norm.cdf(self.d1(), 0.0, 1.0) - self.K * np.exp(-self.r * self.T) * si.norm.cdf(self.d2(), 0.0, 1.0))
    
    def put_option_price(self):
        return (self.K * np.exp(-self.r * self.T) * si.norm.cdf(-self.d2(), 0.0, 1.0) - self.S * si.norm.cdf(-self.d1(), 0.0, 1.0))

# MAIN FUNCTION !!! #
def main():
    
    risk_free_rate, historical_data_period = load_config()
    
    symbol = input("Insert Ticker (es. AAPL, TSLA): ").upper()
    
    current_price, volatility, calls, puts = retrieve(symbol, historical_data_period)
    
    if current_price is not None and volatility is not None:
        expiration_date_str = input("Insert the expiration date of the option (format: YYYY-MM-DD): ")
        expiration_date = datetime.strptime(expiration_date_str, "%Y-%m-%d")
        time_to_expiration = calculate_time_to_expiration(expiration_date)
        strike_price = float(input(f"Insert {symbol}'s strike price (K): "))
        
        # Building our Black-Scholes Model #
        bsm = BlackScholesModel(S=current_price, K=strike_price, T=time_to_expiration, r=risk_free_rate, sigma=volatility)
        
        call_price = bsm.call_option_price()
        put_price = bsm.put_option_price()
        
        print(f"Current Price of the Asset: {current_price}")
        print(f"Hist. Volatility: {volatility}")
        print(f"Call Price: {call_price}")
        print(f"Put Price: {put_price}")
    else:
        print("Can't computate the option pricing due to lack of sufficient information.")

if __name__ == "__main__":
    main()
