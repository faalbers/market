from ..vault import Vault
import pandas as pd
from pprint import pp

class Tickers():
    def __init__(self, symbols=[]):
        self.symbols = set([symbol.upper() for symbol in symbols])
        self.vault = Vault()
    
    @property
    def count(self):
        return len(self.symbols)
    
    def add_symbol(self, symbol):
        self.symbols.add(symbol.upper())
    
    def add_symbols(self, symbols):
        self.symbols.update([symbol.upper() for symbol in symbols])

    # TODO: add scraped symbols
    # TODO: add US market symbols

    def get_symbols(self):
        return sorted(self.symbols)

    def get_profiles(self, update=False):
        return self.vault.get_data(['profile'], self.symbols, update=update)['profile']

    def get_chart(self, start_date=None, end_date=None, update=False):
        chart_data = self.vault.get_data(['chart'], self.symbols, update=update)['chart']
        if 'chart' in chart_data:
            chart_data = chart_data['chart']
        else:
            chart_data = {}

        chart = {}
        for symbol, ts_data in chart_data.items():
            df = pd.DataFrame(ts_data).T
            df.index = pd.to_datetime(df.index, unit='s')
            df.sort_index(inplace=True)
            df.index = df.index.floor('D') # set it to beginning of day
            df = df.drop('timestamp', axis=1)
            if start_date:
                df = df.loc[start_date:]
            if end_date:
                df = df.loc[:end_date]
            chart[symbol] = df
        return chart
        
    def get_news(self):
        # get all available news for tickers
        news = self.vault.get_data(['news'], self.symbols)['news']
        
        symbols_news = {}
        for news_name, news_data in news.items():
            for symbol, ts_data in news_data.items():
                if not symbol in symbols_news:
                    symbols_news[symbol] = ts_data
                else:
                    symbols_news[symbol] = {**symbols_news[symbol], **ts_data}
        for symbol, ts_data in symbols_news.items():
            symbols_news[symbol] = pd.DataFrame(ts_data).T
            symbols_news[symbol].index = pd.to_datetime(symbols_news[symbol].index, unit='s')
            symbols_news[symbol].sort_index(inplace=True)

        return symbols_news

    def get_news_sentiment(self, start_date, end_date):
        news = self.get_news()
        news_sentiment = {}
        for symbol, news_data in news.items():
            news_sentiment[symbol] = news_data['sentiment_llama'].loc[start_date:end_date]
            news_sentiment[symbol].name = 'news_sentiment'
        return news_sentiment
    
    def get_all(self):
        return self.vault.get_data(['all_tickers'], self.symbols)['all_tickers']

    def get_revenue_growth(self):
        return self.vault.get_data(['revenue_growth'], self.symbols)['revenue_growth']
    
    def update(self, catalogs):
        self.vault.update(catalogs, self.symbols)
    
    # TODO: add __str__
