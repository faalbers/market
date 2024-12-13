import requests
from database.keys import KEYS
from ratelimit import limits, sleep_and_retry
from pprint import pp

class Polygon():
    def __init__(self):
        self.init_session()

    def init_session(self):
        # create session
        params = {'apikey': KEYS['POLYGON']['KEY']}
        self.session = requests.Session()
        self.session.params.update(params)

    @sleep_and_retry
    @limits(calls=5, period=70)
    def session_get(self, request_arguments):
        return self.session.get(**request_arguments)
    
    def request(self, request_arguments, push_proc):
        next_request_arguments = request_arguments
        entries = 0
        # runs = 10
        while next_request_arguments:
            response = self.session_get(next_request_arguments)
            if response.headers.get('content-type').startswith('application/json'):
                write_data = {}
                response_data = response.json()
                if 'results' in response_data:
                    push_proc(response_data['results'])
                else:
                    self.logger.info('Polygon: no result in response chunk, stopping requests')
                    break
                if 'count' in response_data:
                    entries += response_data['count']
                self.logger.info('Polygon: entries found: %s' % entries)
                next_request_arguments = None
                if 'next_url' in response_data:
                    next_request_arguments = {'url': response_data['next_url']}
            else:
                next_request_arguments = None
            # print(next_request_arguments)
            # runs -= 1
            # if runs == 0:
            #     next_request_arguments = None
