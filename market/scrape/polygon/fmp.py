import requests
from database.keys import KEYS
from ratelimit import limits, sleep_and_retry
from pprint import pp

class FMP():
    def __init__(self):
        self.init_session()

    def init_session(self):
        # create session
        params = {'apikey': KEYS['FMP']['KEY']}
        self.session = requests.Session()
        self.session.params.update(params)

    @sleep_and_retry
    @limits(calls=250, period=86400)
    def session_get(self, request_arguments):
        return self.session.get(**request_arguments)
    
    def request(self, request_arguments):
        response = self.session_get(request_arguments)
        if response.headers.get('content-type').startswith('application/json'):
            response_data = response.json()
            self.pushAPIData(response_data)
        else:
            self.logger.info('FMP:   unknown request response')
            self.logger.info('FMP:   status code: %s' % (response.status_code))
            self.logger.info('FMP:   content type: %s' % (response.status_code))
