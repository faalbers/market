from market import Market
import logging

def run_this():
    market = Market()
    v = market.vault
    symbols = ['AAPL', 'ANET', 'GRIN', 'BBD', 'CM', 'CWEN', 'SPY', 'BLOIKS', 'GOOG', 'MMM', '^IRX', 'MSFT', 'NVDA', 'ONON', 'SHOP', 'VALE', 'VITAX', 'VZ', 'XOM']
    # symbols = ['AAPL']
    v.update(['test'], symbols)
    logger = logging.getLogger('Market')
    logger.info('last one')
    return

if __name__ == '__main__':
    run_this()
    