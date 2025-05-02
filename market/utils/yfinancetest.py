import yfinance as yf

def yfinancetest():
    ticker = yf.Ticker('AAPL')
    try:
        ticker.fast_info['lastPrice']
    except Exception as e:
        if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
            print('Too Many Requests. Rate limited. Change VPN location')
            return False
    return True
