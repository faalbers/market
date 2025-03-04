from ratelimit import limits, sleep_and_retry
from ...utils import stop_text

class YahooF():
    @sleep_and_retry
    @limits(calls=150, period=60)
    # @limits(calls=2, period=1)
    def exec_proc(self, proc, arguments):
        return proc(**arguments)
    
    def __init__(self):
        return
    
    def multi_execs(self, exec_list):
        count_done = 0
        failed = 0
        failed_total = 0
        for exec in exec_list:
            if (count_done % 100) == 0:
                self.logger.info('YahooF:  to do: %s , failed: %s' % (len(exec_list)-count_done, failed))
                self.db.commit()
                failed = 0
            symbol = exec[0]
            proc = exec[1]
            arguments = exec[2]
            success, result = self.exec_proc(proc, arguments)
            self.push_api_data(symbol, success, result)
            if not success:
                failed += 1
                failed_total += 1
            count_done += 1
            if stop_text():
                self.logger.info('YahooF:  manually stopped multi_exec')
                self.db.commit()
                break
        self.logger.info('YahooF:  done: %s , failed: %s' % (count_done, failed_total))
