import numpy as np
from binance.client import Client
import pandas as pd
import numpy as np

client = Client("", "")

mean_dict = {}
min_dict = {}
max_dict = {}
std_dict = {}
median_dict = {}

spread_mean_dict = {}
spread_min_dict = {}
spread_max_dict = {}
spread_std_dict = {}
spread_median_dict = {}



def funding_rate(symb, limit=1000):
    rate_hist = client.futures_funding_rate(symbol=symb, limit=limit)
    return rate_hist

rate = funding_rate('BTCUSDT')
rate_timestamps = np.array([i['fundingTime'] for i in rate])

def spread_info(symb, first_day):
    data_futures = client.futures_historical_klines(symbol=symb, interval='8h', start_str=first_day, end_str=None, limit=1000)
    data_spot = client.get_historical_klines(symbol=symb,interval='8h',start_str=first_day,limit=1000)

    futures_klines_timestamps = np.array([i[0] for i in data_futures])

    if 0 < int(futures_klines_timestamps[0])-int(first_day) < 1000:

        spot_klines_open = np.array([float(i[1]) for i in data_spot])
        futures_klines_open = np.array([float(i[1]) for i in data_futures])

        spread = futures_klines_open-spot_klines_open
        spread_absolute_return = round(spread[0]/futures_klines_open[0] - spread[-1]/futures_klines_open[-1], 5)
        mean = round(np.mean(spread)/np.mean(futures_klines_open), 5)
        median = round(np.median(spread)/np.median(futures_klines_open), 5)
        min = round(np.min(spread)/np.min(futures_klines_open), 5)
        max = round(np.max(spread)/np.max(futures_klines_open), 5)
        std = round(np.std(spread)/np.std(futures_klines_open), 5)
        return mean, median, min, max, std, spread_absolute_return
    else:
        return np.zeros(6)



#Funding Amount = Nominal Value of Positions × Funding Rate
#(Nominal Value of Positions = Mark Price x Size of a Contract)