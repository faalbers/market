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
        news = self.vault.get_data(['news'], self.symbols)['reference_test']
        print(len(news['AAPL']['news_finviz']))
        print(len(news['AAPL']['news_polygon']))

    # TODO: add __str__
