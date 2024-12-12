from .yahoo import Yahoo
import logging
from ...database import Database
from datetime import datetime, time
from dateutil.relativedelta import relativedelta

class Yahoo_Chart(Yahoo):
    dbName = 'yahoo_chart'

    @staticmethod
    def get_table_names(table_name):
        return [table_name]

    def __init__(self, key_values=[], table_names=[]):
        self.logger = logging.getLogger('vault_multi')
        super().__init__()
        self.db = Database(self.dbName)

        self.logger.info('Yahoo:   Chart: update')
        self.logger.info('Yahoo:   Chart: symbols processing : %s' % len(key_values))

        # create request arguments list
        requests_list = []
        now = datetime.now()
        for symbol in key_values:
            period1 = int((now - relativedelta(years=10)).timestamp())
            period2 = int(now.timestamp())
            request_arguments = {
                'url': 'https://query2.finance.yahoo.com/v8/finance/chart/'+symbol.upper(),
                'params': {
                    'period1': period1,
                    'period2': period2,
                    'interval': '1d',
                    'events': 'div,splits,capitalGains',
                },
                'timeout': 30,
            }                      
            requests_list.append((symbol,request_arguments))
        self.multi_request(requests_list)

        self.logger.info('Yahoo:   Chart: Yahoo_Chart update done')

    def pushAPIData(self, symbol, response_data):
        symbol = symbol.upper()
        if 'chart' in response_data:
            # handle API response
            response_data = response_data['chart']
            if response_data['error']:
                # handle error response
                if response_data['error']['code'] != 'Not Found':
                    self.logger.info('Yahoo:   Chart: %s: %s' % (symbol, response_data['error']['code']))
                return False
            elif response_data['result']:
                # handle data return response
                dfs = []
                response_data = response_data['result'][0]
                chart_data = {}
                if 'timestamp' in response_data:
                    timestamps = response_data['timestamp']
                    if 'indicators' in response_data:
                        # extract all the indicators
                        indicators = response_data['indicators']
                        merged_quote = {**indicators['quote'][0], **indicators['adjclose'][0]}
                        ts_index = 0
                        for timestamp in timestamps:
                            timestamp = datetime.fromtimestamp(timestamp).date()
                            timestamp = int(datetime.combine(timestamp, time()).timestamp())
                            row_data = {}
                            for param in merged_quote.keys():
                                if merged_quote[param][ts_index] != None:
                                    row_data[param] = merged_quote[param][ts_index]
                            if len(row_data) > 0:
                                chart_data[timestamp] = row_data
                            ts_index += 1

                if 'events' in response_data:
                    # extract all the events
                    events = response_data['events']
                    for event, event_data in events.items():
                        for date, date_data in event_data.items():
                            timestamp = datetime.fromtimestamp(date_data['date']).date()
                            timestamp = int(datetime.combine(timestamp, time()).timestamp())
                            if not timestamp in chart_data:
                                chart_data[timestamp] = {}
                            chart_row = chart_data[timestamp]
                            if event == 'dividends':
                                chart_row['dividend'] = date_data['amount']
                            elif event == 'capitalGains':
                                chart_row['capitalGain'] = date_data['amount']
                            elif event == 'splits':
                                chart_row['numerator'] = date_data['numerator']
                                chart_row['denominator'] = date_data['denominator']
                                chart_row['splitRatio'] = date_data['splitRatio']
                

                # write data 
                if len(chart_data) > 0:
                    # make unique table name
                    table_name = 'chart_'
                    for c in symbol:
                        if c.isalnum():
                            table_name += c
                        else:
                            table_name += '_'
                    
                    self.db.table_write(table_name, chart_data, 'timestamp', method='replace')

                    # write table reference
                    self.db.table_write('table_reference', {symbol: {'chart': table_name}}, 'symbol', method='append')
                    return True

        return False

