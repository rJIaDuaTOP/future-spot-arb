import numpy as np
from binance.client import Client
import pandas as pd
import numpy as np

client = Client("", "")

funding_dict = {}
spread_dict = {}
pnl_dict = {}
total_pnl_dict = {}

coins = 'BTC,ETH,GALA,XRP,MATIC,ADA,SOL,LUNA,AVAX,SAND,DOGE,FTM,MANA,AXS,XRP,PEOPLE,DOT,BNB,' \
        'NEAR,ATOM,LTC,LINK,LRC,ADA,FIL,ARPA,DOGE,DYDX,DOT,ALICE,SUSHI,BNB,CRV,ETC,EOS,ONE,SOL,' \
        'XRP,FIL,ICP,LTC,UNI,ROSE,IOTX,ALGO,XLM,XTZ,BCH,VET,HOT,ADA,THETA,LUNA,LINK,EGLD,CHR,SOL,' \
        'ENJ,ZEC,AAVE,TRX,DENT,DOGE,DUSK,CELR,WAVES,ANT,YFI,DODO,TLM,AR,EOS,ENS,RUNE,BNB,CHZ,KNC,' \
        'OMG,1INCH,GRT,UNI,ZIL,SXP,COTI,BCH,EGLD,LINA,MTL,KEEP,GTC,HNT,XMR,BAT,COMP,XLM,MKR,HBAR,KSM,' \
        'BLZ,REEF,SNX,CELO,SRM,KAVA,RSR,NEO,C98,QTUM,DASH,XEM,REN,OCEAN,ETC,IOTA,MASK,IOST,ANKR,' \
        'AUDIO,ZEN,RAY,NKN,SFP,KLAY,CTK,STORJ,RVN,CVC,UNFI,ICX,ONT,NU,LIT,BAND,ALPHA,RLC,ATA,SKL,TRB,' \
        'BEL,AKRO,YFII,OGN,BAKE,ZRX,THETA,STMX,TRX,CTSI,SC,BTS,FLM,TOMO,LPT,BAL,ROSE,DGB'.split(',')

binance_coins = [i.upper() + "USDT" for i in set(coins)]
ftx_coins = [i.upper() + "-PERP" for i in set(coins)]


def funding_rate(symb, limit=1000):
    rate_hist = client.futures_funding_rate(symbol=symb, limit=limit)
    return rate_hist


def statistics_calculation(symb):
    try:
        funding_list = []
        data = funding_rate(symb=symb)
        for i in data:
            funding_list.append(float(i['fundingRate']))
        first_date = str(data[0]['fundingTime'])
        second_date = str(data[1]['fundingTime'])
        mean = round(np.mean(funding_list), 5)
        median = round(np.median(funding_list), 5)
        min = round(np.min(funding_list), 5)
        max = round(np.max(funding_list), 5)
        std = round(np.std(funding_list), 5)
        return mean, median, min, max, std, funding_list, first_date, second_date
    except Exception as e:
        print(e)
        return list(np.zeros(8))


def spread_info(symb, first_day, second_day):
    data_futures = client.futures_historical_klines(symbol=symb, interval='8h', start_str=first_day, end_str=None,
                                                    limit=1000)
    data_spot = client.get_historical_klines(symbol=symb, interval='8h', start_str=first_day, limit=1000)

    futures_klines_timestamps = np.array([i[0] for i in data_futures])
    if -300000 < int(futures_klines_timestamps[0]) - int(second_day) < 300000:  # take 5 minutes interval
        spot_klines_open = np.array([float(i[1]) for i in data_spot])
        futures_klines_open = np.array([float(i[1]) for i in data_futures])

        spread = futures_klines_open - spot_klines_open
        spread_absolute_return = round(spread[0] / futures_klines_open[0] - spread[-1] / futures_klines_open[-1], 5)
        mean = round(np.mean(spread) / np.mean(futures_klines_open), 5)
        median = round(np.median(spread) / np.median(futures_klines_open), 5)
        min = round(np.min(spread) / np.min(futures_klines_open), 5)
        max = round(np.max(spread) / np.max(futures_klines_open), 5)
        std = round(np.std(spread) / np.std(futures_klines_open), 5)
        return mean, median, min, max, std, spread_absolute_return, futures_klines_open, spot_klines_open
    else:
        return 0


def dict_update(symb):
    stats = statistics_calculation(symb=symb)
    fd = stats[6]
    sd = stats[7]
    spread_stats = spread_info(symb=symb, first_day=fd, second_day=sd)
    if spread_stats != 0:
        funding_dict[symb] = {'mean': stats[0], 'median': stats[1], 'min': stats[2], 'max': stats[3],
                              'std': stats[4], 'data': stats[5][1:]}
        spread_dict[symb] = {'mean': spread_stats[0], 'median': spread_stats[1], 'min': spread_stats[2],
                             'max': spread_stats[3],
                             'std': spread_stats[4], 'abs_ret': spread_stats[5], 'futures': spread_stats[6],
                             'spot': spread_stats[7]}
    else:
        return 0


def naive_back_test(symb, usd_balance):
    acquired_funding = 0
    coins_bought = (usd_balance / 2) / float(spread_dict[symb]['spot'][0])
    futures_sold = (usd_balance / 2) / float(spread_dict[symb]['futures'][0])
    if len(funding_dict[symb]['data']) == len(spread_dict[symb]['futures']):
        for i in range(len(funding_dict[symb]['data'])):
            acquired_funding += futures_sold * float(spread_dict[symb]['futures'][i]) * float(
                funding_dict[symb]['data'][i])
        spot_pnl = coins_bought * float(spread_dict[symb]['spot'][-1]) - coins_bought * float(
            spread_dict[symb]['spot'][0])
        futures_pnl = futures_sold * float(spread_dict[symb]['futures'][0]) - futures_sold * float(
            spread_dict[symb]['futures'][-1])
        spread_pnl = spot_pnl + futures_pnl
        pnl_dict[symb] = {'spread_pnl': spread_pnl, 'acquired_funding': acquired_funding,
                          'total pnl': acquired_funding + spread_pnl}
        total_pnl_dict[symb] = {'total pnl': acquired_funding + spread_pnl}
    else:
        return 0


if __name__ == "__main__":
    for i in binance_coins:
        dict_update(i)
        if dict_update(i) != 0:
            naive_back_test(i, 10000)
        else:
            continue
    mean_dict = {k: v['mean'] for k, v in funding_dict.items() if 'mean' in v}
    total_pnl_dict = dict(sorted(total_pnl_dict.items(), key=lambda item: item[1]['total pnl']))
    mean_dict = dict(sorted(mean_dict.items(), key=lambda item: item[1]))
    print(total_pnl_dict)
    print(mean_dict)
