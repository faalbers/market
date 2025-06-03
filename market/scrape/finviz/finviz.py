# import requests
# from database.keys import KEYS
from finvizfinance.quote import finvizfinance
from ratelimit import limits, sleep_and_retry
import pandas as pd
from pprint import pp

class Finviz():
    def __init__(self):
        pass

    @sleep_and_retry
    @limits(calls=3, period=1)
    def get_news_limited(self, symbol):
        try:
            ticker = finvizfinance(symbol)
            news = ticker.ticker_news()
        except Exception as e:
            # self.logger.error("Finviz:  ticker news error: %s: %s" % (symbol, e))
            return (False, pd.DataFrame())
        return (True, news)
    
    def request_news(self, symbol):
        symbol_news = self.get_news_limited(symbol)
        if len(symbol_news) > 0:
            self.pushAPIData(symbol, symbol_news)

