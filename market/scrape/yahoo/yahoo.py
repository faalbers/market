import requests, os, pickle
from datetime import datetime
from dateutil.relativedelta import relativedelta
from ratelimit import limits, sleep_and_retry
from . import const
from pprint import pp

class Yahoo():
    def __init__(self):
        self.init_session()
    
    def init_session(self):
        # get yahoo session cookie and crumb
        # if they dont exist or if they are expired, refresh
        yconfig_file = 'database/yahoo.pickle'
        yconfig = None
        headers = {'User-Agent': const.YAHOO_USER_AGENT}
        if os.path.exists(yconfig_file):
            with open(yconfig_file, 'rb') as f:
                yconfig = pickle.load(f)
            if (datetime.now() + relativedelta(months=1)).timestamp() > yconfig['cookie'].expires:
                yconfig = None
        if not yconfig:
            self.logger.info('Yahoo: refresh cookie and crumb')
            session = requests.Session()
            session.headers.update(headers)
            response = session.get(url='https://fc.yahoo.com')
            cookie = list(response.cookies)[0]
            response = session.get(url='https://query1.finance.yahoo.com/v1/test/getcrumb')
            content_type = response.headers.get('content-type')
            if response.status_code == 200 and content_type.startswith('text/plain'):
                crumb = response.text
                yconfig = {'cookie': cookie, 'crumb': crumb}
                print(yconfig)
                with open(yconfig_file, 'wb') as f:
                    pickle.dump(yconfig, f, protocol=pickle.HIGHEST_PROTOCOL)
            else:
                print(response.status_code)
                print(response.headers.get('content-type'))
                print(response.text)
                raise ValueError('Yahoo: did not get crumb')
        
        # create session with auth cookie
        cookies = {yconfig['cookie'].name: yconfig['cookie'].value}
        params = {'crumb': yconfig['crumb']}
        headers = {'User-Agent': const.YAHOO_USER_AGENT}
        self.session = requests.Session()
        self.session.cookies.update(cookies)
        self.session.params.update(params)
        self.session.headers.update(headers)

    @sleep_and_retry
    @limits(calls=150, period=60)
    def session_get(self, request_arguments):
        return self.session.get(**request_arguments)

    def multi_request(self, requests_list):
        count_done = 0
        failed = 0
        failed_total = 0
        for symbol, request_arguments in requests_list:
            if (count_done % 10) == 0:
                self.logger.info('Yahoo: to do: %s , failed: %s' % (len(requests_list)-count_done, failed))
                failed = 0
            response = self.session_get(request_arguments)
            if response.headers.get('content-type').startswith('application/json'):
                response_data = response.json()['quoteSummary']
                if response_data['error']:
                    if response_data['error']['code'] == 'Not Found':
                        failed += 1
                        failed_total += 1
                    else:
                        self.logger.info('Yahoo: %s: %s' % (symbol, response_data['error']['code']))
                elif response_data['result']:
                    self.pushAPIData(symbol, response_data['result'][0])
            else:
                self.logger.info('Yahoo: %s: unknown request response' % symbol)
                self.logger.info('Yahoo: %s: status code: %s' % (symbol, response.status_code))
                self.logger.info('Yahoo: %s: content type: %s' % (symbol, response.status_code))
            count_done += 1
        self.logger.info('Yahoo: done: %s , failed: %s' % (len(requests_list), failed_total))