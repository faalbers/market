from ratelimit import limits, sleep_and_retry
from ...utils import stop_text
import yfinance as yf

class YahooF():
    @sleep_and_retry
    @limits(calls=100, period=60) # 6000/hour
    def exec_proc(self, proc, arguments):
        return proc(**arguments)
    
    def __init__(self):
        return
    
    def multi_execs(self, exec_list, yfinance_ok=False):
        count_done = 0
        failed = 0
        failed_total = 0
        for exec in exec_list:
            if (count_done % 100) == 0:
                self.logger.info('YahooF:  to do: %s , failed: %s' % (len(exec_list)-count_done, failed))
                self.db.commit()
                failed = 0
            symbol = exec[0]
            procs = exec[1]
            arguments = exec[2]
            ticker = yf.Ticker(symbol)
            arguments['ticker'] = ticker
            result = [False, None, None]
            for proc in procs:
                proc_handle = proc(arguments['data'])
                arguments['data'] = proc_handle[2]
                if proc_handle[0]:
                    result = self.exec_proc(proc_handle[1], arguments)
                    arguments['data'] = result
            self.push_api_data(symbol, arguments['data'])
            if not arguments['data'][0]:
                failed += 1
                failed_total += 1
            count_done += 1
            if stop_text():
                self.logger.info('YahooF:  manually stopped multi_exec')
                self.db.commit()
                break
            if (count_done % 100) == 0:
                if yfinance_ok:
                    if not self.yfinance_ok():
                        break
                    else:
                        self.logger.info('YahooF:  yfinance still ok ...')
        self.logger.info('YahooF:  done: %s , failed: %s' % (count_done, failed_total))

    def yfinance_ok(self):
        ticker = yf.Ticker('AAPL')
        try:
            ticker.fast_info['lastPrice']
        except Exception as e:
            if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                self.logger.info('YahooF:  Too Many Requests. Rate limited. Change VPN location')
                return False
        return True