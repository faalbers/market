from market import Market
from pprint import pp
from datetime import datetime
import pandas as pd

if __name__ == '__main__':
    m = Market()
    q = m.get_quicken('database/2020.QIF')
    symbols = q.get_securities()['symbol'].unique()
    # print(symbols)
    data = m.vault.get_data(['price'], symbols, update=True)['price']
    dftn = pd.DataFrame(data).T['price'].dropna()
    pp(dftn)
    dftn.to_csv('Z:\\Quicken\\QuickenImport.csv', header=False, sep=',', encoding='utf-8')
    del(m)


