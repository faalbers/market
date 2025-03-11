from market import Market
from pprint import pp
from datetime import datetime
import pandas as pd
import yfinance as yf

def run_this():
    m = Market()
    q = m.get_quicken('database/2020.QIF')
    symbols = q.get_securities()['symbol'].unique()
    # print(symbols)
    # data = m.vault.get_data(['price'], symbols, update=True)['price']
    # dftn = pd.DataFrame(data).T['price'].dropna()
    dftn = pd.Series()
    for symbol in symbols:
        if symbol in  [None, 'Cash'] or symbol.startswith('912'): continue
        ticker = yf.Ticker(symbol)
        try:
            price = ticker.fast_info['lastPrice']
            print(symbol, ticker.fast_info['lastPrice'])
            dftn[symbol] = price
        except:
            pass
    dftn = dftn.dropna().round(2)
    
    dftn.to_csv('Z:\\Quicken\\QuickenImport.csv', header=False, sep=',', encoding='utf-8')
    # dftn.to_csv('woohoo.csv', header=False, sep=',', encoding='utf-8')
    del(m)

if __name__ == '__main__':
    run_this()

