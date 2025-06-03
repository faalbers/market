import logging
from ...database import Database
from database.keys import KEYS
from fredapi import Fred as Fred_API
import pandas as pd
import numpy as np
from pprint import pp
from ...utils import storage

# https://fred.stlouisfed.org/

class Fred():
    dbName = 'fred'

    @staticmethod
    def get_data_names(data_name):
        if data_name == 'all':
            return ['fred']
        return [data_name]

    def __init__(self, key_values=[], data_names=[], update = False, forced=False):
        self.db = Database(self.dbName)
        if not update: return
        self.logger = logging.getLogger('vault_multi')
        self.fred = Fred_API(api_key=KEYS['FRED']['KEY'])

        observation_start = '1971-01-01'
        self.logger.info('Fred:    FED update starting from: %s' % observation_start)
        indicators = {
            'gdp': 'GDPC1',
            'interest_rate': 'FEDFUNDS',
            'unemployment': 'UNRATE',
            'cpi': 'CPIAUCSL',
            'pce': 'PCEPI',
            'nonfarm_payrolls': 'PAYEMS', 
            'corporate_profits': 'CP',
            'money_suply': 'M2SL',
            'consumer_confidence': 'UMCSENT',
            'housing_starts': 'HOUST',
            'permits': 'PERMIT',
        }

        fred_data = {key: self.fred.get_series(value, observation_start=observation_start) for key, value in indicators.items()}
        macro_data = pd.DataFrame(fred_data)
        macro_data.index = np.array([int(dt.timestamp()) for dt in macro_data.index.to_pydatetime()])
        macro_data = macro_data.T.to_dict()

        self.db.table_write('fred', macro_data, key_name='timestamp', method='replace')
        self.logger.info('Fred:    FED update done')

