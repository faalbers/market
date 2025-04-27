from .etrade import Etrade
from ...database import Database
from ...utils import stop_text
import logging
from pprint import pp
from datetime import datetime

class Etrade_Quote(Etrade):
    dbName = 'etrade_quote'

    @staticmethod
    def get_table_names(table_name):
        if table_name == 'all':
            return ['quote']
        return [table_name]

    def __init__(self, key_values=[], table_names=[]):
        self.logger = logging.getLogger('vault_multi')
        super().__init__()
        self.db = Database(self.dbName)

        # if self.session == None:
        #     self.logger.info('Etrade:  Quote: Session did no succeed')

        # check what symbols need to be updated
        symbols = self.update_check(key_values)
        # symbols = key_values
        
        if len(symbols) == 0: return
        self.init_session()

        self.logger.info('Etrade:  Quote: update')
        self.logger.info('Etrade:  Quote: symbols processing : %s' % len(symbols))

        # backup first
        self.db.backup()
        
        # create symbol blocks
        block_size = 50
        block_end = 0
        symbol_blocks = []
        for block_idx in range(int(len(symbols)/block_size)):
            block_start = block_idx*block_size
            block_end = block_start+block_size
            symbol_blocks.append(symbols[block_start:block_end])
        if len(symbols)%block_size > 0:
            symbol_blocks.append(symbols[block_end:])
        
        # go through symbol blocks and retrieve data
        count_done = 0
        failed = 0
        failed_total = 0
        for symbol_block in symbol_blocks:
            if (count_done % 100) == 0:
                self.logger.info('Etrade:  to do: %s , failed: %s' % (len(symbols)-count_done, failed))
                self.db.commit()
                failed = 0
            
            equities = {}
            failed = 0
            # get ALL
            # symbols_string = ','.join(symbol_block)
            symbols_string = ','.join([x.lstrip('^') for x in symbol_block])
            print(symbol_block)
            print(symbols_string)
            request_arguments = {
                'url': 'https://api.etrade.com/v1/market/quote/%s.json' % symbols_string,
                'params': {
                    'detailFlag': 'ALL',
                    'overrideSymbolCount': 'true',
                },
            }

            mutual_funds = set()
            response = self.session_get(request_arguments)
            if response.headers.get('content-type').startswith('application/json'):
                response_data = response.json()
                if 'QuoteResponse' in response_data:
                    response_data = response_data['QuoteResponse']
                    if 'QuoteData' in response_data:
                        for quote_data in response_data['QuoteData']:
                            product = quote_data['Product']
                            # symbol = product['symbol']
                            symbol = self.match_symbol(product['symbol'], symbol_block)
                            security_type = product['securityType']
                            if 'securitySubType' in product:
                                security_type = product['securitySubType']
                            if security_type in ['MF', 'MMF']:
                                mutual_funds.add(symbol)
                            else:
                                equities[symbol] = quote_data['All']
                                equities[symbol]['securityType'] = security_type
                                equities[symbol]['dateTimeUTC'] = quote_data['dateTimeUTC']

            if len(mutual_funds) > 0:
                # get MF_DETAIL
                # symbols_string = ','.join(mutual_funds)
                symbols_string = ','.join([x.lstrip('^') for x in mutual_funds])
                request_arguments = {
                    'url': 'https://api.etrade.com/v1/market/quote/%s.json' % symbols_string,
                    'params': {
                        'detailFlag': 'MF_DETAIL',
                        'overrideSymbolCount': 'true',
                    },
                }

                response = self.session_get(request_arguments)
                if response.headers.get('content-type').startswith('application/json'):
                    response_data = response.json()
                    if 'QuoteResponse' in response_data:
                        response_data = response_data['QuoteResponse']
                        if 'QuoteData' in response_data:
                            for quote_data in response_data['QuoteData']:
                                product = quote_data['Product']
                                # symbol = product['symbol']
                                symbol = self.match_symbol(product['symbol'], mutual_funds)
                                security_type = product['securityType']
                                equities[symbol] = quote_data['MutualFund']
                                equities[symbol]['securityType'] = security_type
                                equities[symbol]['dateTimeUTC'] = quote_data['dateTimeUTC']

            # push into database
            for symbol in symbol_block:
                if not symbol in equities:
                    failed += 1
                    self.push_api_data(symbol, [False, None, 'no data'])
                else:
                    self.push_api_data(symbol, [True, equities[symbol], 'ok'])
            count_done += len(symbol_block)
            failed_total += failed
            self.db.commit()
            
            # manually stop if needed
            if stop_text():
                self.logger.info('Etrade:  manually stopped multi_exec')
                break
        
        self.logger.info('Etrade:  done: %s , failed: %s' % (count_done, failed_total))
        self.logger.info('Etrade:  update done')

    def update_check(self, symbols):
        db_status = self.db.table_read('status_db')
        
        # found is 5 days check
        found_update = int(datetime.now().timestamp()) - (3600 * 24 * 5)
        # not found is 1/2 year check
        not_found_update = int(datetime.now().timestamp()) - (3600 * 24 * 182)

        update_symbols = []
        for symbol in symbols:
            if not symbol in db_status:
                # never done before, add it
                update_symbols.append(symbol)
            else:
                if db_status[symbol]['found']:
                    # found before, only do again after 24 h
                    if db_status[symbol]['timestamp'] <= found_update: update_symbols.append(symbol)
                else:
                    # not found before, only try again after 1/2 year
                    if db_status[symbol]['timestamp'] <= not_found_update: update_symbols.append(symbol)

        return update_symbols

    def match_symbol(self, symbol, symbol_block):
        if symbol in symbol_block:
            return symbol
        symbol = '^' + symbol
        if symbol in symbol_block:
            return symbol
        return None

    def push_api_data(self, symbol, result):
        timestamp = int(datetime.now().timestamp())
        found = result[0]
        status_info = {
            'timestamp': timestamp,
            'found': found,
            'message': str(result[2])
        }

        self.db.table_write('status_db', {symbol: status_info}, key_name='symbol', method='update')
        if not found:
            return
        result = result[1]
        
        result['timestamp'] = timestamp
        self.db.table_write('quote', {symbol: result}, key_name='symbol', method='replace')
