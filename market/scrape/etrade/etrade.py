from ...utils import stop_text
from rauth import OAuth1Service
from ratelimit import limits, sleep_and_retry
from database.keys import KEYS
import webbrowser, time
from pprint import pp

class Etrade():
    @sleep_and_retry
    @limits(calls=2, period=1)
    def session_get(self, request_arguments):
        response = self.session.get(**request_arguments)
        return response

    def __init__(self):
        self.session = None

    def init_session(self):
        etrade = OAuth1Service(
            name="etrade",
            consumer_key=KEYS['ETRADE']['KEY'],
            consumer_secret=KEYS['ETRADE']['SECRET'],
            request_token_url="https://api.etrade.com/oauth/request_token",
            access_token_url="https://api.etrade.com/oauth/access_token",
            authorize_url="https://us.etrade.com/e/t/etws/authorize?key={}&token={}",
            base_url='https://api.etrade.com')
        
        request_token, request_token_secret = etrade.get_request_token(
            params={"oauth_callback": "oob", "format": "json"})

        authorize_url = etrade.authorize_url.format(etrade.consumer_key, request_token)
        webbrowser.open(authorize_url)
        
        # fill code in etrade_code.txt
        # TODO this needs a better sollution
        text_code = 'CODE'
        with open('etrade_code.txt', 'w') as f:
            f.write('CODE')
            f.close()
        with open('etrade_code.txt', 'r') as f:
            while text_code == 'CODE':
                time.sleep(1)
                text_code = f.readline().split('\n')[0].strip()
                f.seek(0)
            f.close()
        print('|%s|' % text_code)
        if text_code == 'STOP':
            self.session = None
        else:
            self.session = etrade.get_auth_session(request_token,
                                            request_token_secret,
                                            params={"oauth_verifier": text_code})


    def __del__(self):
        if self.session == None: return
        
        url = 'https://api.etrade.com/oauth/revoke_access_token'
        try:
            self.session.get(url)
            self.logger.info('Etrade: revoke access')
        except:
            self.logger.info('Etrade: revoke access failed')

