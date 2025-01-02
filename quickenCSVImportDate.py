from market import Market
from pprint import pp
from datetime import datetime
import pandas as pd

def run_this():
    end_date = '2020-12-31'
    start_date = pd.to_datetime(end_date) - pd.Timedelta(days=7)

    m = Market()
    q = m.get_quicken('database/2020.QIF')
    symbols = q.get_securities()['symbol'].unique()

    # print(symbols)
    t = m.get_tickers(symbols)
    chart_symbols = t.get_chart(start_date, end_date, update=True)
    dftn = pd.Series()
    for symbol, chart in chart_symbols.items():
        if symbol == 'CASH': continue
        if chart.empty: continue
        dftn[symbol] = chart.iloc[-1]['close']
    pp(dftn)
    dftn.to_csv('Z:\\Quicken\\QuickenImport_%s.csv' % end_date, header=False, sep=',', encoding='utf-8')
    del(m)

if __name__ == '__main__':
    run_this()
