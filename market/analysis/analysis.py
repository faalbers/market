from ..tickers import Tickers
from ..viz import Viz
import pandas as pd
from pprint import pp
from ..vault import Vault

class Analysis():
    def __init__(self, symbols):
        self.tickers = Tickers(symbols)
        self.benchmarks = Tickers(['SPY', 'QQQ'])
        self.viz = Viz()
        self.vault = Vault()
        
    def news_sentiment(self):
        start_date = '2023-01-01'
        end_date = '2025-01-31'
        chart = self.tickers.get_chart(start_date, end_date)
        sp_500_growth = self.benchmarks.get_chart(start_date, end_date)['SPY']['adjclose']
        sp_500_growth = (sp_500_growth / sp_500_growth.iloc[0]) - 1.0
        news_sentiment = self.tickers.get_news_sentiment(start_date, end_date)
        test_df = {}
        for symbol in self.tickers.get_symbols():
            if symbol in chart and symbol in news_sentiment:
                symbol_growth = chart[symbol]['adjclose']
                symbol_growth = (symbol_growth / symbol_growth.iloc[0]) - 1.0
                symbol_growth = symbol_growth - sp_500_growth
                ns = news_sentiment[symbol][news_sentiment[symbol].ne('NEUTRAL')]
                df = pd.merge(symbol_growth, ns, left_index=True, right_index=True, how='outer')
                weekly_groups = df.groupby(pd.Grouper(freq='W'))
                df_data = pd.DataFrame()
                for name, group in weekly_groups:
                    df_data.loc[name, 'adjclose'] = group['adjclose'].dropna().mean()
                    value_counts = group['news_sentiment'].value_counts()
                    positive = 0
                    negative = 0
                    if 'POSITIVE' in value_counts:
                        positive = group['news_sentiment'].value_counts()['POSITIVE']
                    if 'NEGATIVE' in value_counts:
                        negative = group['news_sentiment'].value_counts()['NEGATIVE']
                    sentiment = positive + negative
                    if sentiment > 0:
                        sentiment = ((positive / sentiment) * 2.0) - 1.0
                    # df_data.loc[name, 'P'] = positive
                    # df_data.loc[name, 'N'] = negative
                    df_data.loc[name, 'sentiment'] = sentiment
                
                test_df[symbol] = df_data
        self.viz.plot_timeseries(test_df)

    def revenue_growth(self):
        # all_tickers = self.tickers.get_all()
        # self.viz.data_keys_text(all_tickers, rename_set=set(self.tickers.get_symbols()), rename_to='symbol')
        
        # all_other = self.vault.get_data(['all_other'])['all_other']
        # self.viz.data_keys_text(all_other, file_name='data_other_keys')

        revenue = self.tickers.get_revenue_growth()
        pp(revenue.keys())


