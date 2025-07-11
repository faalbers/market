from ratelimit import limits, sleep_and_retry
from ...utils import stop_text, yfinancetest
import yfinance as yf

class YahooF():
    @sleep_and_retry
    @limits(calls=100, period=60) # 6000/hour
    def exec_proc(self, proc, arguments):
        return proc(**arguments)
    
    def __init__(self):
        return
    
    def multi_execs(self, exec_list, parent_name=''):
        # TODO add parent name to log
        count_done = 0
        failed = 0
        failed_total = 0
        for exec in exec_list:
            if (count_done % 100) == 0:
                self.logger.info('YahooF:  %s: to do: %s , failed: %s' % (parent_name, len(exec_list)-count_done, failed))
                self.db.commit()
                failed = 0
            # gather symbol, procs to be handled and arguments
            symbol = exec[0]
            procs = exec[1]
            arguments = exec[2]
            
            # create a ticker object and set it in the arguments
            ticker = yf.Ticker(symbol)
            arguments['ticker'] = ticker

            # set inital return of procs to be handled
            result = [False, None, None]
            for proc in procs:
                # handle main proc
                proc_handle = proc(arguments['data'])

                # set the current data
                arguments['data'] = proc_handle[2]
                # check if we need to run this yfinance proc
                if proc_handle[0]:
                    # run yfinance proc with time liimits
                    result = self.exec_proc(proc_handle[1], arguments)
                    # retrieve data and set it
                    arguments['data'] = result
            # once all yfinance procs are done, push the data
            self.push_api_data(symbol, arguments['data'])
            if not arguments['data'][0]:
                failed += 1
                failed_total += 1
            count_done += 1
            
            # manually stop if needed
            if stop_text():
                self.logger.info('YahooF:  %s: manually stopped multi_exec' % parent_name)
                self.db.commit()
                break

            # run a yfinance test every 100 entriesexec entries
            if (count_done % 100) == 0:
                if not yfinancetest():
                    self.logger.info('YahooF:  %s: yfinance not ok ...' % parent_name)
                    break
                else:
                    self.logger.info('YahooF:  %s: yfinance still ok ...' % parent_name)
        self.logger.info('YahooF:  %s: done: %s , failed: %s' % (parent_name, count_done, failed_total))
