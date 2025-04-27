from ...utils import stop_text
from rauth import OAuth1Service
from ratelimit import limits, sleep_and_retry
from database.keys import KEYS
import webbrowser, time

class Etrade():
    @sleep_and_retry
    @limits(calls=4, period=1)
    def session_get(self, request_arguments):
        response = self.session.get(**request_arguments)
        # print(response.text)
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



        # # get yahoo session cookie and crumb
        # # if they dont exist or if they are expired, refresh
        # yconfig_file = 'database/yahoo.pickle'
        # yconfig = None
        # # headers = {'User-Agent': const.YAHOO_USER_AGENT}
        # # headers = {'User-Agent': random.choice( const.YAHOO_USER_AGENTS)}
        # headers = {'User-Agent': const.YAHOO_USER_AGENTS[1]}
        # if os.path.exists(yconfig_file):
        #     with open(yconfig_file, 'rb') as f:
        #         yconfig = pickle.load(f)
        #     if (datetime.now() + relativedelta(months=1)).timestamp() > yconfig['cookie'].expires:
        #         yconfig = None
        # if not yconfig:
        #     self.logger.info('Yahoo: refresh cookie and crumb')
        #     session = requests.Session()
        #     session.headers.update(headers)
        #     response = session.get(url='https://fc.yahoo.com')
        #     cookie = list(response.cookies)[0]
        #     response = session.get(url='https://query1.finance.yahoo.com/v1/test/getcrumb')
        #     content_type = response.headers.get('content-type')
        #     if response.status_code == 200 and content_type.startswith('text/plain'):
        #         crumb = response.text
        #         yconfig = {'cookie': cookie, 'crumb': crumb}
        #         print(yconfig)
        #         with open(yconfig_file, 'wb') as f:
        #             pickle.dump(yconfig, f, protocol=pickle.HIGHEST_PROTOCOL)
        #     else:
        #         print(response.status_code)
        #         print(response.headers.get('content-type'))
        #         print(response.text)
        #         raise ValueError('Yahoo: did not get crumb')
        
        # # create session with auth cookie
        # cookies = {yconfig['cookie'].name: yconfig['cookie'].value}
        # params = {'crumb': yconfig['crumb']}
        # headers = {'User-Agent': const.YAHOO_USER_AGENT}
        # self.session = requests.Session()
        # self.session.cookies.update(cookies)
        # self.session.params.update(params)
        # self.session.headers.update(headers)
