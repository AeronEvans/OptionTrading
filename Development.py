import requests
import numpy as np
from math import log, sqrt, exp
from statistics import NormalDist
import time




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




def get_option_market(API_KEY, ticker,expiration, strike, contract="call"):
    #print("\n\nGet Option Market results: \n")
    #url = f"https://api.polygon.io/v3/reference/options/contracts?underlying_ticker={ticker}&contract_type=call&expiration_date={expiration}&strike_price.gte={strike}&limit=1&apiKey={API_KEY}"
    url = f"https://api.polygon.io/v3/reference/options/contracts?underlying_ticker={ticker}&contract_type={contract}&expiration_date={expiration}&strike_price.gte={strike}&limit=1&apiKey={API_KEY}"

    response = requests.get(url)
    data = response.json()
    for i in data['results']:
        #print(i), "\n"
        return get_option_contract_data(API_KEY, i['ticker'])






def get_option_contract_data(API_KEY, option_code):
    url = f"https://api.polygon.io/v2/aggs/ticker/{option_code}/prev?adjusted=true&apiKey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    print(data)
    #print("\n\nGet option contract data results: \n")
    #print(data["results"])
    return(data["results"][0]["c"])





def main():
    
    API_KEY = "OhOis7n5SskS5OswmI7kqgqow66tCtiT"
    global date
    date = "2025-02-13"
    ticker = "TSLA"
    expiration = "2025-02-21"
    current_price = get_stock_price(API_KEY, ticker)


    target_price = int(input(f"Current stock price is {current_price}, pick a target price:"))


    if target_price > current_price*1.3:
        print("Suggested strategy: Bullish Call")
        call_price = get_option_market(API_KEY, ticker, expiration, target_price)
        print("price of strategy:", call_price)
    elif target_price > current_price*1.02:
        print("Suggested strategy: Bull Call Spread")
        long_call_price = get_option_market(API_KEY, ticker, expiration, target_price)
        short_call_price = get_option_market(API_KEY, ticker, expiration, target_price*1.1)
        print("price of strategy:", long_call_price-short_call_price)

    elif target_price < current_price*0.98:
        print("Suggested strategy: Bear Put Spread")


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
        












if __name__ == "__main__":
    main()