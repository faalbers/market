import yfinance as yf

def yfinancetest():
    ticker = yf.Ticker('AAPL')
    try:
        quoteType = ticker.fast_info['quoteType']
        if len(quoteType) == 0: return False
    except Exception as e:
        if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
            print('Too Many Requests. Rate limited. Change VPN location')
            return False
    return True
