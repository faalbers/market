from .etrade import Etrade
from ...database import Database
from ...utils import stop_text
import logging
from pprint import pp
from datetime import datetime
import pandas as pd

class Etrade_Quote(Etrade):
    dbName = 'etrade_quote'

    @staticmethod
    def get_data_names(data_name):
        if data_name == 'all':
            return ['quote']
        return [data_name]

    def __init__(self, key_values=[], data_names=[], update = False, forced=False):
        self.db = Database(self.dbName)
        super().__init__()
        if not update: return
        self.logger = logging.getLogger('vault_multi')

        # if self.session == None:
        #     self.logger.info('Etrade:  Quote: Session did no succeed')

        # check what symbols need to be updated
        if forced:
            symbols = sorted(key_values)
        else:
            symbols = self.update_check(key_values)
        if len(symbols) == 0: return
        
        self.init_session()

        self.logger.info('Etrade:  Quote: update')
        self.logger.info('Etrade:  Quote: symbols processing : %s' % len(symbols))

        # backup first
        self.logger.info('Etrade:  Quote: %s' % self.db.backup())
        
        # create symbol blocks
        block_size = 50
        block_end = 0
        symbol_blocks = []
        for block_idx in range(int(len(symbols)/block_size)):
            block_start = block_idx*block_size
            block_end = block_start+block_size
            symbol_blocks.append(symbols[block_start:block_end])
        if len(symbols) % block_size > 0:
            symbol_blocks.append(symbols[block_end:])

        # go through symbol blocks and retrieve data
        count_done = 0
        failed = 0
        failed_total = 0
        for symbol_block in symbol_blocks:
            if (count_done % (block_size*2)) == 0:
                self.logger.info('Etrade:  to do: %s , failed: %s' % (len(symbols)-count_done, failed))
                self.db.commit()
                failed = 0
            
            equities = {}
            failed = 0
            # get ALL
            # symbols_string = ','.join(symbol_block)
            symbols_string = ','.join([x.lstrip('^') for x in symbol_block])
            request_arguments = {
                'url': 'https://api.etrade.com/v1/market/quote/%s.json' % symbols_string,
                'params': {
                    'detailFlag': 'ALL',
                    'overrideSymbolCount': 'true',
                },
            }

            mutual_funds = set()
            try:
                response = self.session_get(request_arguments)
            except Exception as e:
                self.logger.info('Etrade:  ALL session get error: %s' % (str(e)))
                self.logger.info('Etrade:  stopping')
                self.logger.info('Etrade:  done: %s , failed: %s' % (count_done, failed_total))
                self.db.commit()
                return
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
            else:
                print(mutual_funds)
                print(symbols_string)
                pp(response.text)
                self.db.commit()
                raise ValueError('no json content type on ALL')
            
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

                try:
                    response = self.session_get(request_arguments)
                except Exception as e:
                    self.logger.info('Etrade:  MF_DETAIL session get error: %s' % (str(e)))
                    self.logger.info('Etrade:  stopping')
                    self.logger.info('Etrade:  done: %s , failed: %s' % (count_done, failed_total))
                    self.db.commit()
                    return
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
                else:
                    print(mutual_funds)
                    print(symbols_string)
                    pp(response.text)
                    self.db.commit()
                    raise ValueError('no json content type on MF_DETAIL')

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
        timestamp_pdt = int(datetime.now().timestamp())

        one_month_ts = timestamp_pdt - (3600 * 24 * 31)
        half_year_ts = timestamp_pdt - (3600 * 24 * 182)

        status_db = self.db.table_read('status_db', keys=symbols)
        if status_db.shape[0] == 0: return sorted(symbols)

        # found and last read more then one month ago
        one_month = (status_db['found'] > 0) & (status_db['timestamp'] < one_month_ts)
        
        # not found and last read more then a half year ago
        one_year = (status_db['found'] == 0) & (status_db['timestamp'] < half_year_ts)
        
        # checked from status_db
        status_check = set(status_db[one_month ^ one_year].index.tolist())

        # not read
        not_read = set(symbols).difference(set(status_db.index))

        return sorted(not_read.union(status_check))

    def match_symbol(self, symbol, symbol_block):
        if symbol in symbol_block:
            return symbol
        symbol = '^' + symbol
        if symbol in symbol_block:
            return symbol
        return None

    def push_api_data(self, symbol, result):
        found = result[0]
        message = result[2]
        result = result[1]

        timestamp = int(datetime.now().timestamp())
        status = {
            'timestamp': timestamp,
            'found': found,
            'message': str(message)
        }
        status = pd.DataFrame([status], index=[symbol])
        status.index.name = 'symbol'
        self.db.table_write('status_db', status)
        
        if not found:return

        result = pd.DataFrame([result], index=[symbol])
        result.index.name = 'symbol'
        self.db.table_write('quote', result)

    def get_vault_data(self, data_name, columns, key_values):
        if data_name == 'quote':
            if len(columns) > 0:
                column_names = [x[0] for x in columns]
                # data = self.db.table_read_df('quote', columns=column_names, key_values=key_values, index_column='symbol')
                data = self.db.table_read('quote', keys=key_values, columns=column_names)
                data = data.rename(columns={x[0]: x[1] for x in columns})
                return data
            else:
                # data = self.db.table_read_df('quote', key_values=key_values, index_column='symbol')
                data = self.db.table_read('quote', keys=key_values)
                return data
    
    def get_vault_params(self, data_name):
        if data_name == 'quote':
            column_types = self.db.get_table_info('quote')['columnTypes']
            column_types.pop('symbol')
            return column_types
