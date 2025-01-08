import configparser
import yfinance as yf
import numpy as np
import datetime
from datetime import datetime
import scipy.stats as si
import os
import csv

def load_config():
    config = configparser.ConfigParser()
    config.read("config.ini")
    risk_free_rate = float(config["DEFAULT"].get("risk_free_rate", 0.05)) # Default Value 5%  
    historical_data_period = config["DEFAULT"].get("historical_data_period", "1y") # Default Time-Frame 1yr
    return risk_free_rate, historical_data_period  

def retrieve(symbol, historical_data_period):
    try:
        ticker = yf.Ticker(symbol)
        close_prices = ticker.history(period=historical_data_period)['Close'].tolist() 
        current_price = close_prices[-1]
        historical_data = ticker.history(period=historical_data_period)


        returns = np.log(historical_data['Close'] / historical_data['Close'].shift(1)).dropna() 
        volatility = np.std(returns) * np.sqrt(252)  # 252 are the average trading days in the US
        
    
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

def quickOption():
    
    risk_free_rate, historical_data_period = load_config()
    
    symbol = input("Insert Ticker (es. AAPL, TSLA): ").upper()
    
    current_price, volatility, calls, puts = retrieve(symbol, historical_data_period)
    
    if current_price is not None and volatility is not None:
        expiration_date_str = input("Insert the expiration date of the option (format: YYYY-MM-DD): ")
        expiration_date = datetime.strptime(expiration_date_str, "%Y-%m-%d")
        time_to_expiration = calculate_time_to_expiration(expiration_date)

                
        strike_price_input = input(f"Insert {symbol}'s strike price (K) or type 'ATM' if strike_price = current_price: ").strip()

     
        if strike_price_input.upper() == "ATM":
            strike_price = current_price
            print(f"Using ATM strike price: {strike_price}")

        else:
            try:
                strike_price = float(strike_price_input)
            except ValueError:
                print("Invalid input for strike price. Please enter a number or 'ATM'.")
                return


    
        bsm = BlackScholesModel(S=current_price, K=strike_price, T=time_to_expiration, r=risk_free_rate, sigma=volatility)
        
        call_price = bsm.call_option_price()
        put_price = bsm.put_option_price()
        call_option_code = generate_option_code(symbol,expiration_date,"C",strike_price)
        put_option_code = generate_option_code(symbol,expiration_date,"P",strike_price)
        
        print(f"Current Price of the Asset: {current_price}")
        print(f"Hist. Volatility: {volatility}")
        print(f"{call_option_code} Call Price: {call_price}")
        print(f"{put_option_code} Put Price: {put_price}")
    else:
        print("Can't compute the option pricing due to lack of sufficient information.")



def optionPrice(ticker, exp, k="ATM", option_type="C"):
    risk_free_rate, historical_data_period = load_config()
    current_price, volatility, _, _ = retrieve(ticker, historical_data_period)
    
    if current_price is None or volatility is None:
        print("Unable to retrieve data for option pricing.")
        return None

    expiration_date = datetime.strptime(exp, "%Y-%m-%d")
    time_to_expiration = calculate_time_to_expiration(expiration_date)

    if k=="ATM":
        strike_price=current_price
    else:
        strike_price=float(k)

    bsm = BlackScholesModel(S=current_price, K=strike_price, T=time_to_expiration, r=risk_free_rate, sigma=volatility)

    if option_type.upper() == "C":
        return float(bsm.call_option_price())
    elif option_type.upper() == "P":
        return float(bsm.put_option_price())
    else:
        raise ValueError("Invalid option type. Use 'call' or 'put'.")

def optionSummary(ticker, K="ATM", length=10, export_csv="N"):
    risk_free_rate, historical_data_period = load_config()
    current_price, volatility, _, _ = retrieve(ticker, historical_data_period)

    if current_price is None or volatility is None:
        print("Unable to retrieve data for option summary.")
        return []

    ticker_obj = yf.Ticker(ticker)
    expiration_dates = ticker_obj.options
    summary = []

    for exp in expiration_dates[:length]:
        try:
            expiration_date = datetime.strptime(exp, "%Y-%m-%d")
            time_to_expiration = calculate_time_to_expiration(expiration_date)

            if K == "ATM":
                strike_price = current_price
            else:
                strike_price = K

            # Create the Black-Scholes model and calculate the prices
            bsm = BlackScholesModel(S=current_price, K=strike_price, T=time_to_expiration, r=risk_free_rate, sigma=volatility)
            call_price = bsm.call_option_price()
            put_price = bsm.put_option_price()

            # Append the data to the summary list
            summary.append([exp, call_price, put_price])
        except Exception as e:
            print(f"Error processing expiration date {exp}: {e}")
            continue
        
    # CSV Export logic
    if export_csv.upper() == "Y":
        try:
            current_directory = os.path.dirname(os.path.abspath(__file__))
            new_file_path = os.path.join(current_directory, f'{ticker}.csv')

            with open(new_file_path, mode="w", newline="") as file:
                writer = csv.writer(file)
                # Write headers
                writer.writerow(["Expiration Date", "Call Price", "Put Price"])
                # Write data rows
                writer.writerows(summary)

            print(f"Data exported to {new_file_path}")
        except Exception as e:
            print(f"Error exporting data to CSV: {e}")

    return summary





def generate_option_code(symbol, expiration_date, option_type, strike_price):
    
    # Validate inputs
    if len(symbol) > 6:
        raise ValueError("Symbol cannot exceed 6 characters.")
    if option_type not in ('C', 'P'):
        raise ValueError("Option type must be 'C' for Call or 'P' for Put.")
    
    # Extract year, month, and day from the datetime object
    year_str = f"{expiration_date.year % 100:02d}"  # Last two digits of the year
    month_str = f"{expiration_date.month:02d}"
    day_str = f"{expiration_date.day:02d}"

    # Format strike price with 5 digits before and 3 after the decimal
    strike_price_str = f"{strike_price:09.3f}".replace('.', '')

    # Concatenate all parts to form the option code
    option_code = f"{symbol.upper()}{year_str}{month_str}{day_str}{option_type}{strike_price_str}"
    return option_code

