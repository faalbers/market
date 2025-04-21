from datetime import datetime
from pprint import pp
import os
import pandas as pd

class Merrill_Lynch_V2():
    name = 'Merrill_Lynch_V2'

    def __init__(self, statement):
        self.statement = statement
        self.accounts = {}

        # if self.statement.pdf_file != 'database/statements_ml\\7WA 15527-2012-01-03.pdf': return

        # return

        # print('')
        # print('%s: %s' % (self.name, self.statement.pdf_file))

        self.accounts = {
            '7WA-15527': {
                'type': 'INDIVIDUAL INVESTOR ACCOUNT',
                'statement': self.statement.pdf_file,
                'holdings': {
                    'DISNEY (WALT) CO COM STK': {
                        'type': 'stock',
                        'symbol': 'DIS',
                        'cusip': None,
                        'quantity': 122.0,
                        'transactions': []
                    }
                }
            }
        }

        # HACK biggest one yet
        if os.path.basename(self.statement.pdf_file) == '7WA 15527-2010-01-03.pdf':
            self.accounts['7WA-15527']['start_date'] = datetime(2010, 1, 1, 0, 0)
            self.accounts['7WA-15527']['end_date'] = datetime(2010, 3, 31, 0, 0)
            disney = self.accounts['7WA-15527']['holdings']['DISNEY (WALT) CO COM STK']
            disney['date'] = datetime(2010, 3, 31, 0, 0)
            disney['transactions'].append(
                {
                    'transaction_date': datetime(2010, 2, 11, 0, 0),
                    'type': 'Journal Entry',
                    'quantity': 122.0,
                    # 'price': 7.38,
                })
        elif os.path.basename(self.statement.pdf_file) == '7WA 15527-2010-04-06.pdf':
            self.accounts['7WA-15527']['start_date'] = datetime(2010, 4, 1, 0, 0)
            self.accounts['7WA-15527']['end_date'] = datetime(2010, 6, 30, 0, 0)
            disney = self.accounts['7WA-15527']['holdings']['DISNEY (WALT) CO COM STK']
            disney['date'] = datetime(2010, 6, 30, 0, 0)
            
        elif os.path.basename(self.statement.pdf_file) == '7WA 15527-2010-07-09.pdf':
            self.accounts['7WA-15527']['start_date'] = datetime(2010, 7, 1, 0, 0)
            self.accounts['7WA-15527']['end_date'] = datetime(2010, 9, 30, 0, 0)
            disney = self.accounts['7WA-15527']['holdings']['DISNEY (WALT) CO COM STK']
            disney['date'] = datetime(2010, 9, 30, 0, 0)

        elif os.path.basename(self.statement.pdf_file) == '7WA 15527-2010-10-12.pdf':
            self.accounts['7WA-15527']['start_date'] = datetime(2010, 10, 1, 0, 0)
            self.accounts['7WA-15527']['end_date'] = datetime(2010, 12, 31, 0, 0)
            disney = self.accounts['7WA-15527']['holdings']['DISNEY (WALT) CO COM STK']
            disney['date'] = datetime(2010, 12, 31, 0, 0)

        # pp(self.accounts)