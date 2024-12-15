from .vault import Vault
import pandas as pd
from pprint import pp

class Tickers():
    def __init__(self, symbols=[]):
        self.symbols = set([symbol.upper() for symbol in symbols])
        self.vault = Vault()
    
    def add_symbol(self, symbol):
        self.symbols.add(symbol.upper())
    
    def add_symbols(self, symbols):
        self.symbols.update([symbol.upper() for symbol in symbols])

    # TODO: add scraped symbols
    # TODO: add US market symbols

    def get_symbols(self):
        return sorted(self.symbols)

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

    # TODO: add __str__
