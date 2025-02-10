from datetime import datetime
from pprint import pp
import math
import pandas as pd

class Etrade():
    name = 'Etrade'

    def __init__(self, statement):
        self.statement = statement
        print('')
        print('%s: %s' % (self.name, self.statement.pdf_file))

        # get fundamental data
        self.start_date = None
        self.end_date = None
        self.account_name = None
        self.account_type = None
        start_page = None
        for page_num, blocks in self.statement.get_blocks().items():
            for block in blocks:
                if block[0].startswith('Account Number:'):
                    start_page = page_num
                    self.account_name = block[0].split(':')[-1].strip()
                    self.account_type = block[2].split(':')[-1].strip()
                    date = block[1].split(':')[-1].strip()
                    date = date.split('-')
                    self.start_date = datetime.strptime(date[0].strip(), '%B %d, %Y')
                    self.end_date = datetime.strptime(date[1].strip(), '%B %d, %Y')

                    break
            if self.account_name != None: break
                    
        # print('Account Name: %s' % self.account_name)
        # print('Account Type: %s' % self.account_type)
        # print('Start Date: %s' % self.start_date)
        # print('End Date: %s' % self.end_date)

        self.transactions = []
        self.get_chunks(start_page)
        self.get_activity()

        # pp(self.transactions)

    def get_chunks(self, start_page):
        chunk_names = ['ACCOUNT HOLDINGS', 'TRANSACTION HISTORY']
        current_chunk = None
        current_subchunk = None
        self.chunks = {}
        for page_num in range(2, self.statement.page_count):
            for block in self.statement.get_page_blocks(page_num):
                if block[0] in chunk_names:
                    # print('\t%s' % block[0])
                    current_chunk = block[0]
                    # print('\t%s' % current_chunk)
                    current_subchunk = None
                    continue
                if current_chunk == 'ACCOUNT HOLDINGS':
                    if block[0].startswith('TREASURIES'):
                        if current_subchunk != 'TREASURIES':
                            current_subchunk = 'TREASURIES'
                            # print('\t\t%s' % current_subchunk)
                            self.chunks[current_subchunk] = []
                            continue
                    if block[0].startswith('MUTUAL FUNDS'):
                        if current_subchunk != 'MUTUAL FUNDS':
                            current_subchunk = 'MUTUAL FUNDS'
                            # print('\t\t%s' % current_subchunk)
                            self.chunks[current_subchunk] = []
                            continue
                    if current_subchunk != None and (block[0].startswith('TOTAL ') or block[0].startswith('NET ')):
                        current_subchunk = None
                        continue

                if current_chunk == 'TRANSACTION HISTORY':
                    if block[0] == 'SECURITIES PURCHASED OR SOLD':
                        current_subchunk = 'SECURITIES PURCHASED OR SOLD'
                        # print('\t\t%s' % current_subchunk)
                        self.chunks[current_subchunk] = []
                        continue
                    if block[0] == 'MUTUAL FUNDS PURCHASED OR SOLD':
                        current_subchunk = 'MUTUAL FUNDS PURCHASED OR SOLD'
                        # print('\t\t%s' % current_subchunk)
                        self.chunks[current_subchunk] = []
                        continue
                    if block[0] == 'DIVIDENDS & INTEREST ACTIVITY':
                        current_subchunk = 'DIVIDENDS & INTEREST ACTIVITY'
                        # print('\t\t%s' % current_subchunk)
                        self.chunks[current_subchunk] = []
                        continue
                    if block[0] == 'WITHDRAWALS & DEPOSITS':
                        current_subchunk = 'WITHDRAWALS & DEPOSITS'
                        # print('\t\t%s' % current_subchunk)
                        self.chunks[current_subchunk] = []
                        continue
                    if block[0] == 'CONTRIBUTIONS & DISTRIBUTIONS ACTIVITY':
                        current_subchunk = 'CONTRIBUTIONS & DISTRIBUTIONS ACTIVITY'
                        # print('\t\t%s' % current_subchunk)
                        self.chunks[current_subchunk] = []
                        continue
                    if block[0] == 'OTHER ACTIVITY':
                        current_subchunk = 'OTHER ACTIVITY'
                        # print('\t\t%s' % current_subchunk)
                        self.chunks[current_subchunk] = []
                        continue
                    if current_subchunk != None and (block[0].startswith('TOTAL ') or block[0].startswith('NET ')):
                        current_subchunk = None
                        continue

                if current_subchunk in self.chunks:
                    for line in block:
                        self.chunks[current_subchunk].append(line)

    def get_activity(self):
        for chunk_name, lines in self.chunks.items():
            if chunk_name in [
                'SECURITIES PURCHASED OR SOLD',
                'MUTUAL FUNDS PURCHASED OR SOLD',
                'DIVIDENDS & INTEREST ACTIVITY',
                'WITHDRAWALS & DEPOSITS',
                'CONTRIBUTIONS & DISTRIBUTIONS ACTIVITY',
                'OTHER ACTIVITY',
            ]:
                self.get_transactions(lines, chunk_name)

    def get_transactions(self, lines, chunk_name):
        last_index = None
        current_transaction = {}
        for line_index in range(len(lines)):
            line = lines[line_index]
            line_digits = line.replace('/', '')
            if line_digits.isdigit() and line != line_digits and len(line_digits) == 6:
                # create a datetime object from the date line
                date = datetime.strptime(line, '%m/%d/%y')

                if last_index != None:
                    # check index difference between date line and last date line
                    diff_index = line_index - last_index
                    if diff_index <= 2:
                        # looks like we have a Settlement Date
                        current_transaction['SettlementDate'] = date
                    else:
                        # we got to the next Transaction Date
                        # store the last one and create a new one
                        self.parse_transaction(current_transaction, chunk_name)
                        self.transactions.append(current_transaction)
                        current_transaction = {'TransactionDate': date, 'lines': []}
                else:
                    # this is the first Transaction Date, create a new one
                    current_transaction = {'TransactionDate': date, 'lines': []}
                
                # set index since last date line
                last_index = line_index
            elif 'TransactionDate' in current_transaction:
                # ignore '12:34' time line
                if not(len(line) == 5 and line.replace(':', '').isdigit()):
                    current_transaction['lines'].append(line)
        
        # make sure the last transaction is added if needed
        if 'TransactionDate' in current_transaction:
            self.parse_transaction(current_transaction, chunk_name)
            self.transactions.append(current_transaction)

    def parse_transaction(self, transaction, chunk_name):
        self.trim_transaction_lines(transaction)
        lines = transaction.pop('lines')
        if chunk_name in ['SECURITIES PURCHASED OR SOLD', 'MUTUAL FUNDS PURCHASED OR SOLD']:
            last_string_index = self.get_last_string_index(lines)
            transaction['TransactionType'] = lines[last_string_index]
            transaction['Description'] = ' '.join(lines[0:(last_string_index-1)])
            transaction['Symbol'] = lines[last_string_index-1]
            transaction['Quantity'] = self.get_float(lines[last_string_index+1])
            transaction['Price'] = self.get_float(lines[last_string_index+2])
            transaction['Amount'] = self.get_float(lines[-1])
            if transaction['TransactionType'] == 'Bought':
                transaction['Amount'] *= -math.copysign(1, transaction['Quantity'])

        if chunk_name in ['DIVIDENDS & INTEREST ACTIVITY', 'CONTRIBUTIONS & DISTRIBUTIONS ACTIVITY', 'WITHDRAWALS & DEPOSITS']:
            transaction['TransactionType'] = lines[0]
            transaction['Amount'] = self.get_float(lines[-1])
            
            # handle the ones with symbol
            if transaction['TransactionType'] in ['Dividend', 'Capital Gain']:
                transaction['Description'] = ' '.join(lines[1:-2])
                transaction['Symbol'] = lines[-2]
            else:
                transaction['Description'] = ' '.join(lines[1:-1])

            # negate amounts
            if transaction['TransactionType'] in ['ACH Debit', 'Conversion', 'Transfer']:
                transaction['Amount'] = -transaction['Amount']
            
            # clear adjustments
            if transaction['TransactionType'] == 'Adjustment': transaction = {}

        if chunk_name in ['OTHER ACTIVITY']:
            last_string_index = self.get_last_string_index(lines)

            # if lines[last_string_index] in ['Dividend', 'Conversion', 'Redemption', 'Reinvest', 'Other']:
            if lines[last_string_index] in ['Conversion', 'Dividend', 'Other']:
                transaction['TransactionType'] = lines[last_string_index]
                transaction['Description'] = ' '.join(lines[0:(last_string_index-1)])
                transaction['Symbol'] = lines[last_string_index-1]
                transaction['Amount'] = self.get_float(lines[-1])

                # pp(transaction, etrade_log)

            if lines[last_string_index] in ['Redemption', 'Reinvest', 'Conversion']:
                transaction['TransactionType'] = lines[last_string_index]
                transaction['Description'] = ' '.join(lines[0:(last_string_index-1)])
                transaction['Symbol'] = lines[last_string_index-1]
                transaction['Quantity'] = self.get_float(lines[last_string_index+1])
                transaction['Amount'] = self.get_float(lines[-2])
                if transaction['TransactionType'] == 'Reinvest':
                    transaction['Amount'] *= -math.copysign(1, transaction['Quantity'])
    
    def trim_transaction_lines(self, transaction):
        index = 0
        for line in transaction['lines']:
            if 'PAGE ' in line and ' OF ' in line:
                transaction['lines'] = transaction['lines'][:index]
                return
            index += 1

    def get_float(self, text):
        if text.startswith('$'): text = text[1:]
        if text.startswith('('): text = '-'+text[1:-1]
        text = text.replace(',', '')
        try:
            return float(text)
        except:
            return None

    def get_last_string_index(self, lines):
            index = 1
            lines_reverse = lines.copy()
            lines_reverse.reverse()
            for line in lines_reverse:
                if self.get_float(line) == None: break
                index += 1
            index = -index
            return index
