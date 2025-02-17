import requests
import numpy as np
from math import log, sqrt, exp
from statistics import NormalDist
import time
import matplotlib.pyplot as plt

def get_stock_price(API_KEY, ticker):
    url = f"https://api.polygon.io/v1/open-close/{ticker}/{date}?adjusted=true&apiKey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print("Ticker: ", ticker)
        print("close price: ", data["close"], " on: ", date)
        return data.get("close")
    else:
        print(f"Error: {response.json()}")
        return None

def get_option_market(API_KEY, ticker, expiration, strike, contract="call"):
    url = f"https://api.polygon.io/v3/reference/options/contracts?underlying_ticker={ticker}&contract_type={contract}&expiration_date={expiration}&strike_price.gte={strike}&limit=1&apiKey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    for i in data['results']:
        return get_option_contract_data(API_KEY, i['ticker'])

def get_option_contract_data(API_KEY, option_code):
    url = f"https://api.polygon.io/v2/aggs/ticker/{option_code}/prev?adjusted=true&apiKey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    print(data)
    return(data["results"][0]["c"])

def plot_strategy_profit(strategy_type, current_price, target_price, prices, profit_function):
    plt.figure(figsize=(10, 6))
    profits = [profit_function(price) for price in prices]
    plt.plot(prices, profits, label=f'{strategy_type} Profit')
    plt.axvline(x=current_price, color='g', linestyle='--', label='Current Price')
    plt.axvline(x=target_price, color='r', linestyle='--', label='Target Price')
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    plt.xlabel('Stock Price at Expiry')
    plt.ylabel('Profit ($)')
    plt.title(f'{strategy_type} Profit vs Stock Price at Expiry')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()

def bullish_call_profit(strike, premium):
    def profit_function(stock_price):
        return max(0, stock_price - strike) - premium
    return profit_function

def bull_call_spread_profit(long_strike, short_strike, long_premium, short_premium):
    def profit_function(stock_price):
        long_payoff = max(0, stock_price - long_strike)
        short_payoff = -max(0, stock_price - short_strike)
        return long_payoff + short_payoff - (long_premium - short_premium)
    return profit_function

def iron_condor_profit(long_call_strike, short_call_strike, short_put_strike, long_put_strike,
                      long_call_premium, short_call_premium, short_put_premium, long_put_premium):
    def profit_function(stock_price):
        long_call_payoff = max(0, stock_price - long_call_strike)
        short_call_payoff = -max(0, stock_price - short_call_strike)
        short_put_payoff = -max(0, short_put_strike - stock_price)
        long_put_payoff = max(0, long_put_strike - stock_price)
        premium_received = short_call_premium + short_put_premium - long_call_premium - long_put_premium
        return long_call_payoff + short_call_payoff + short_put_payoff + long_put_payoff + premium_received
    return profit_function

def main():
    API_KEY = "OhOis7n5SskS5OswmI7kqgqow66tCtiT"
    global date
    date = "2025-02-13"
    ticker = "TSLA"
    expiration = "2025-02-21"
    current_price = get_stock_price(API_KEY, ticker)
    target_price = int(input(f"Current stock price is {current_price}, pick a target price:"))
    
    # Create price range for plotting
    prices = np.linspace(current_price * 0.5, current_price * 1.5, 100)

    if target_price > current_price*1.3:
        print("Suggested strategy: Bullish Call")
        call_price = get_option_market(API_KEY, ticker, expiration, target_price)
        print("price of strategy:", call_price)
        profit_func = bullish_call_profit(target_price, call_price)
        plot_strategy_profit("Bullish Call", current_price, target_price, prices, profit_func)

    elif target_price > current_price*1.02:
        print("Suggested strategy: Bull Call Spread")
        long_call_price = get_option_market(API_KEY, ticker, expiration, target_price)
        short_call_price = get_option_market(API_KEY, ticker, expiration, target_price*1.1)
        print("price of strategy:", long_call_price-short_call_price)
        profit_func = bull_call_spread_profit(target_price, target_price*1.1, 
                                            long_call_price, short_call_price)
        plot_strategy_profit("Bull Call Spread", current_price, target_price, prices, profit_func)

    elif target_price < current_price*0.98:
        print("Suggested strategy: Bear Put Spread")
        # Add Bear Put Spread plotting here if needed
        
    else:
        print("Suggested strategy: Iron Condor")
        long_call_price = get_option_market(API_KEY, ticker, expiration, target_price*1.1)
        print(long_call_price)
        short_call_price = get_option_market(API_KEY, ticker, expiration, target_price*1.05)
        print(short_call_price)
        short_put_price = get_option_market(API_KEY, ticker, expiration, target_price*0.95,"put")
        print(short_put_price)
        long_put_price = get_option_market(API_KEY, ticker, expiration, target_price*0.9,"put")
        print("price of iron condor:", long_call_price+long_put_price-short_call_price-short_put_price)
        
        profit_func = iron_condor_profit(target_price*1.1, target_price*1.05,
                                       target_price*0.95, target_price*0.9,
                                       long_call_price, short_call_price,
                                       short_put_price, long_put_price)
        plot_strategy_profit("Iron Condor", current_price, target_price, prices, profit_func)

if __name__ == "__main__":
    main()