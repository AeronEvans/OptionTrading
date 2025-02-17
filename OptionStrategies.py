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
    return(data["results"][0]["c"])

def plot_strategy_profit(strategy_type,current_price,target_price,prices,profit_function):
    plt.style.use('seaborn-v0_8-pastel')
    plt.figure(figsize=(12,8),dpi=100)
    profits=[profit_function(price) for price in prices]
    plt.plot(prices,profits,label=f'{strategy_type} Profit',linewidth=2.5,color='#2E86C1')
    plt.axvline(x=current_price,color='#27AE60',linestyle='--',linewidth=1.5,label='Current Price',alpha=0.8)
    plt.axvline(x=target_price,color='#E74C3C',linestyle='--',linewidth=1.5,label='Target Price',alpha=0.8)
    plt.axhline(y=0,color='#7F8C8D',linestyle='-',linewidth=1,alpha=0.5)
    plt.grid(True,linestyle='--',alpha=0.7)
    plt.xlabel('Stock Price at Expiry',fontsize=12,fontweight='bold',fontfamily='sans-serif')
    plt.ylabel('Profit ($)',fontsize=12,fontweight='bold',fontfamily='sans-serif')
    plt.title(f'{strategy_type} Profit vs Stock Price at Expiry',fontsize=14,fontweight='bold',fontfamily='sans-serif',pad=20)
    plt.legend(loc='upper left',frameon=True,fancybox=True,shadow=True,fontsize=10)
    plt.fill_between(prices,profits,0,where=(np.array(profits)>0),color='#A9DFBF',alpha=0.3,label='Profit Zone')
    plt.fill_between(prices,profits,0,where=(np.array(profits)<0),color='#F5B7B1',alpha=0.3,label='Loss Zone')
    plt.tight_layout()
    max_profit=max(profits)
    min_profit=min(profits)
    plt.annotate(f'Max Profit: ${max_profit:.2f}',xy=(prices[profits.index(max_profit)],max_profit),xytext=(10,10),textcoords='offset points',fontsize=9,bbox=dict(facecolor='white',edgecolor='gray',alpha=0.7))
    plt.annotate(f'Max Loss: ${min_profit:.2f}',xy=(prices[profits.index(min_profit)],min_profit),xytext=(10,-10),textcoords='offset points',fontsize=9,bbox=dict(facecolor='white',edgecolor='gray',alpha=0.7))
    ax=plt.gca()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,p:f'${x:,.0f}'))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x,p:f'${x:,.0f}'))
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

def bear_put_spread_profit(long_strike, short_strike, long_premium, short_premium):
    def profit_function(stock_price):
        long_payoff = max(0, long_strike - stock_price)
        short_payoff = -max(0, short_strike - stock_price)
        return long_payoff + short_payoff - (long_premium - short_premium)
    return profit_function


def main():
    API_KEY = "OhOis7n5SskS5OswmI7kqgqow66tCtiT"
    global date
    date = "2025-02-13"
    ticker = "AAPL"
    expiration = "2025-02-21"
    current_price = get_stock_price(API_KEY, ticker)
    target_price = int(input(f"Current stock price is {current_price}, pick a target price:"))
    
    # Create price range for plotting
    prices = np.linspace(current_price * 0.5, current_price * 1.5, 100)

    if target_price > current_price * 1.3:
        print("Suggested strategy: Bullish Call")
        call_price = get_option_market(API_KEY, ticker, expiration, target_price)
        print(f"Bought Call Option: {ticker} {expiration} {target_price}C for ${call_price:.2f}")
        print("Price of strategy:", call_price)
        profit_func = bullish_call_profit(target_price, call_price)
        plot_strategy_profit("Bullish Call", current_price, target_price, prices, profit_func)

    elif target_price > current_price * 1.02:
        print("Suggested strategy: Bull Call Spread")
        long_strike = target_price * 0.9
        short_strike = target_price * 1.1
        long_call_price = get_option_market(API_KEY, ticker, expiration, long_strike)
        short_call_price = get_option_market(API_KEY, ticker, expiration, short_strike)
        print(f"Bought Call Option: {ticker} {expiration} {long_strike}C for ${long_call_price:.2f}")
        print(f"Sold Call Option: {ticker} {expiration} {short_strike}C for ${short_call_price:.2f}")
        print("Price of strategy:", long_call_price - short_call_price)
        profit_func = bull_call_spread_profit(long_strike, short_strike, long_call_price, short_call_price)
        plot_strategy_profit("Bull Call Spread", current_price, target_price, prices, profit_func)

    elif target_price < current_price * 0.98:
        print("Suggested strategy: Bear Put Spread")
        long_strike = target_price * 1.1
        short_strike = target_price * 0.9
        long_put_price = get_option_market(API_KEY, ticker, expiration, long_strike, "put")
        short_put_price = get_option_market(API_KEY, ticker, expiration, short_strike, "put")
        print(f"Bought Put Option: {ticker} {expiration} {long_strike}P for ${long_put_price:.2f}")
        print(f"Sold Put Option: {ticker} {expiration} {short_strike}P for ${short_put_price:.2f}")
        print("Price of strategy:", long_put_price - short_put_price)
        profit_func = bear_put_spread_profit(long_strike, short_strike, long_put_price, short_put_price)
        plot_strategy_profit("Bear Put Spread", current_price, target_price, prices, profit_func)

    else:
        print("Suggested strategy: Iron Condor")
        long_call_strike = target_price * 1.1
        short_call_strike = target_price * 1.05
        short_put_strike = target_price * 0.95
        long_put_strike = target_price * 0.9

        long_call_price = get_option_market(API_KEY, ticker, expiration, long_call_strike)
        short_call_price = get_option_market(API_KEY, ticker, expiration, short_call_strike)
        short_put_price = get_option_market(API_KEY, ticker, expiration, short_put_strike, "put")
        long_put_price = get_option_market(API_KEY, ticker, expiration, long_put_strike, "put")

        print(f"Bought Call Option: {ticker} {expiration} {long_call_strike}C for ${long_call_price:.2f}")
        print(f"Sold Call Option: {ticker} {expiration} {short_call_strike}C for ${short_call_price:.2f}")
        print(f"Sold Put Option: {ticker} {expiration} {short_put_strike}P for ${short_put_price:.2f}")
        print(f"Bought Put Option: {ticker} {expiration} {long_put_strike}P for ${long_put_price:.2f}")
        print("Price of iron condor:", long_call_price + long_put_price - short_call_price - short_put_price)

        profit_func = iron_condor_profit(long_call_strike, short_call_strike, short_put_strike, long_put_strike,
                                        long_call_price, short_call_price, short_put_price, long_put_price)
        plot_strategy_profit("Iron Condor", current_price, target_price, prices, profit_func)



if __name__ == "__main__":
    main()
