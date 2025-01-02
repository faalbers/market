from ..tickers import Tickers
import pandas as pd

class Analysis():
    def __init__(self, symbols):
        self.tickers = Tickers(symbols)
        
    def test(self):
        start_date = '2024-01-01'
        end_date = '2025-01-31'
        adj_close = self.tickers.get_adj_close(start_date, end_date)
        news_sentiment = self.tickers.get_news_sentiment(start_date, end_date)
        for symbol in self.tickers.get_symbols():
            if symbol in adj_close and symbol in news_sentiment:
                ns = news_sentiment[symbol][news_sentiment[symbol].ne('NEUTRAL')]
                df = pd.merge(adj_close[symbol], ns, left_index=True, right_index=True, how='outer')
                weekly_groups = df.groupby(pd.Grouper(freq='W'))
                df_data = pd.DataFrame()
                for name, group in weekly_groups:
                    df_data.loc[name, 'adj_close'] = group['adj_close'].dropna().mean()
                    positive = group['news_sentiment'].value_counts()['POSITIVE']
                    negative = group['news_sentiment'].value_counts()['NEGATIVE']
                    sentiment = positive + negative
                    if sentiment > 0:
                        sentiment = ((positive / sentiment) * 2.0) - 1.0
                    # df_data.loc[name, 'P'] = positive
                    # df_data.loc[name, 'N'] = negative
                    df_data.loc[name, 'sentiment'] = sentiment
                
                print(df_data)
