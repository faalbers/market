from datetime import datetime
from pprint import pp
import math
import pandas as pd

class Morgan_Stanley():
    name = 'Morgan Stanley'

    def __init__(self, statement):
        self.statement = statement
        print(statement.pdf_file)

        # get period dates
        self.start_date = None
        self.end_date = None
        for block in self.statement.get_page_blocks(0):
            if block[0].startswith('Beginning Total Value'):
                self.start_date = datetime.strptime(block[0].split('as of ')[-1].strip(')'), '%m/%d/%y')
                self.end_date = datetime.strptime(block[2].split('as of ')[-1].strip(')'), '%m/%d/%y')

        # find account pages
        account_summary_pages = []
        account_detail_pages = []
        for page_num, blocks in self.statement.get_blocks().items():
            for block in blocks:
                if block[0].startswith('Account Summary'):
                    account_summary_pages.append(page_num)
                    break
                if block[0].startswith('Account Detail'):
                    account_detail_pages.append(page_num)
                    break

        # get account summary
        self.account_name = None
        self.account_type = None
        blocks = self.statement.get_page_blocks(account_summary_pages[0])
        for block_idx in range(len(blocks)):
            if blocks[block_idx][0] =='Morgan Stanley at Work Self-Directed Account':
                self.account_type = blocks[block_idx][0]
                self.account_name = blocks[block_idx+1][0]
                break
            if blocks[block_idx][0] =='Self-Directed Retirement Account':
                self.account_type = blocks[block_idx][0]
                self.account_name = blocks[block_idx+1][0]
                break
            if blocks[block_idx][0] =='Active Assets Account':
                self.account_type = blocks[block_idx][0]
                self.account_name = blocks[block_idx+1][0]
                break

        # print('Account Name: %s' % self.account_name)
        # print('Account Type: %s' % self.account_type)
        # print('Start Date: %s' % self.start_date)
        # print('End Date: %s' % self.end_date)

        # get account detail
        self.holdings = {}
        self.transactions = []
        self.get_chunks(account_detail_pages)
        self.get_holdings()
        self.get_activity()

        # pp(self.holdings)
        pp(self.transactions)

    def get_chunks(self, account_detail_pages):
        chunk_names = ['HOLDINGS', 'ACTIVITY', 'MESSAGES']
        current_chunk = None
        current_subchunk = None
        chunk_lines = {}
        for page_num in account_detail_pages:
            for block in self.statement.get_page_blocks(page_num):
                if block[0] in chunk_names:
                    current_chunk = block[0]
                    # print('\t%s' % current_chunk)
                    current_subchunk = None
                    continue
                if current_chunk == 'HOLDINGS':
                    if block[0] == 'COMMON STOCKS':
                        current_subchunk = 'COMMON STOCKS'
                        # print('\t\t%s' % current_subchunk)
                        chunk_lines[current_subchunk] = []
                        continue
                    if block[0] == 'TREASURY SECURITIES':
                        current_subchunk = 'TREASURY SECURITIES'
                        # print('\t\t%s' % current_subchunk)
                        chunk_lines[current_subchunk] = []
                        continue
                    if block[0] == 'OPEN-END MUTUAL FUNDS':
                        current_subchunk = 'OPEN-END MUTUAL FUNDS'
                        # print('\t\t%s' % current_subchunk)
                        chunk_lines[current_subchunk] = []
                        continue
                    if block[0] == 'CASH, BANK DEPOSIT PROGRAM AND MONEY MARKET FUNDS':
                        current_subchunk = 'CASH, BANK DEPOSIT PROGRAM AND MONEY MARKET FUNDS'
                        # print('\t\t%s' % current_subchunk)
                        chunk_lines[current_subchunk] = []
                        continue
                    if block[0] == 'CERTIFICATES OF DEPOSIT':
                        current_subchunk = 'CERTIFICATES OF DEPOSIT'
                        # print('\t\t%s' % current_subchunk)
                        chunk_lines[current_subchunk] = []
                        continue
                    if block[0] == 'OPEN-END NON-SWEEP MONEY MARKET FUNDS':
                        current_subchunk = 'OPEN-END NON-SWEEP MONEY MARKET FUNDS'
                        # print('\t\t%s' % current_subchunk)
                        chunk_lines[current_subchunk] = []
                        continue
                    if block[0] == 'ALLOCATION OF ASSETS':
                        current_subchunk = None
                        continue
                if current_chunk == 'ACTIVITY':
                    if block[0] == 'CASH FLOW ACTIVITY BY DATE':
                        current_subchunk = 'CASH FLOW ACTIVITY BY DATE'
                        # print('\t\t%s' % current_subchunk)
                        chunk_lines[current_subchunk] = []
                        continue
                    if block[0] == 'MONEY MARKET FUND (MMF) AND BANK DEPOSIT PROGRAM ACTIVITY':
                        current_subchunk = 'MONEY MARKET FUND (MMF) AND BANK DEPOSIT PROGRAM ACTIVITY'
                        # print('\t\t%s' % current_subchunk)
                        chunk_lines[current_subchunk] = []
                        continue
                    if block[0] == 'SECURITY TRANSFERS':
                        current_subchunk = 'SECURITY TRANSFERS'
                        # print('\t\t%s' % current_subchunk)
                        chunk_lines[current_subchunk] = []
                        continue
                    if block[0] == 'CORPORATE ACTIONS':
                        current_subchunk = 'CORPORATE ACTIONS'
                        # print('\t\t%s' % current_subchunk)
                        chunk_lines[current_subchunk] = []
                        continue
                    if block[0] == 'UNSETTLED PURCHASES/SALES ACTIVITY':
                        current_subchunk = 'UNSETTLED PURCHASES/SALES ACTIVITY'
                        # print('\t\t%s' % current_subchunk)
                        chunk_lines[current_subchunk] = []
                        continue
                    if block[0] in ['NET CREDITS/(DEBITS)', 'NET ACTIVITY FOR PERIOD',
                            'TOTAL SECURITY TRANSFERS', 'NET UNSETTLED PURCHASES/SALES', 'Account Detail']:
                        current_subchunk = None
                        continue

                if current_subchunk in chunk_lines:
                    for line in block:
                        chunk_lines[current_subchunk].append(line)

        self.chunks = chunk_lines

    def get_holdings(self):
        if 'COMMON STOCKS' in self.chunks:
            lines = self.chunks['COMMON STOCKS']
            for line_index in range(len(lines)):
                line = lines[line_index]
                if line.isupper() and ' (' in line:
                    splits = line.split(' (')
                    self.holdings[splits[0]] = {'type': 'STOCK', 'symbol': splits[1][:-1]}
        if 'OPEN-END MUTUAL FUNDS' in self.chunks:
            lines = self.chunks['OPEN-END MUTUAL FUNDS']
            for line_index in range(len(lines)):
                line = lines[line_index]
                if line.isupper() and ' (' in line:
                    splits = line.split(' (')
                    self.holdings[splits[0]] = {'type': 'MUTUAL FUND', 'symbol': splits[1][:-1]}
        if 'OPEN-END NON-SWEEP MONEY MARKET FUNDS' in self.chunks:
            lines = self.chunks['OPEN-END NON-SWEEP MONEY MARKET FUNDS']
            for line_index in range(len(lines)):
                line = lines[line_index]
                if line.isupper() and ' (' in line:
                    splits = line.split(' (')
                    self.holdings[splits[0]] = {'type': 'MONEY MARKET FUND', 'symbol': splits[1][:-1]}
        if 'TREASURY SECURITIES' in self.chunks:
            lines = self.chunks['TREASURY SECURITIES']
            for line_index in range(len(lines)):
                line = lines[line_index]
                if line.isupper():
                    if (len(lines)-line_index) > 1:
                        next_line = lines[line_index+1]
                        if 'CUSIP' in next_line:
                            cusip = next_line.split('CUSIP ')[1].strip()
                            self.holdings[line+' '+cusip] = {'type': 'TREASURY BILL', 'symbol': cusip}
        if 'CERTIFICATES OF DEPOSIT' in self.chunks:
            lines = self.chunks['CERTIFICATES OF DEPOSIT']
            for line_index in range(len(lines)):
                line = lines[line_index]
                if line.isupper():
                    if (len(lines)-line_index) > 1:
                        next_line = lines[line_index+1]
                        if 'CUSIP' in next_line:
                            cusip = next_line.split('CUSIP ')[1].strip()
                            self.holdings[line+' '+cusip] = {'type': 'CERTIFICATES OF DEPOSIT', 'symbol': cusip}

    def get_activity(self):
        for chunk_name, lines in self.chunks.items():
            if chunk_name in [
                'CASH FLOW ACTIVITY BY DATE',
                'MONEY MARKET FUND (MMF) AND BANK DEPOSIT PROGRAM ACTIVITY',
                'SECURITY TRANSFERS',
                'CORPORATE ACTIONS',    
                'UNSETTLED PURCHASES/SALES ACTIVITY',    
            ]:
                # print('\t\t%s' % chunk_name)
                # for line in lines:
                #     print('\t\t%s' % line)
                self.get_transactions(lines)

    def get_transactions(self, lines):
        last_index = None
        current_transaction = {}
        for line_index in range(len(lines)):
            line = lines[line_index]
            line_digits = line.replace('/', '')
            if line_digits.isdigit() and line != line_digits and len(line_digits) <= 4:
                # create a datetime object from the date line
                date_elements = line.split('/')
                date = datetime(month=int(date_elements[0]), day=int(date_elements[1]), year=self.end_date.year)

                if last_index != None:
                    # check index difference between date line and last date line
                    diff_index = line_index - last_index
                    if diff_index == 1:
                        # looks like we have a Settlement Date
                        current_transaction['SettlementDate'] = date
                    else:
                        # we got to the next Transaction Date
                        # store the last one and create a new one
                        self.parse_transaction(current_transaction)
                        self.transactions.append(current_transaction)
                        current_transaction = {'TransactionDate': date, 'lines': []}
                else:
                    # this is the first Transaction Date, create a new one
                    current_transaction = {'TransactionDate': date, 'lines': []}
                
                # set index since last date line
                last_index = line_index
            elif 'TransactionDate' in current_transaction:
                current_transaction['lines'].append(line)
        
        # make sure the last transaction is added if needed
        if 'TransactionDate' in current_transaction:
            # trim lines if needed
            self.parse_transaction(current_transaction)
            self.transactions.append(current_transaction)

    def trim_transaction_lines(self, transaction):
        try:
            index = transaction['lines'].index('Account Detail')
            transaction['lines'] = transaction['lines'][:index]
        except:
            pass

    def parse_transaction(self, transaction):
        # self.trim_transaction_lines(transaction)
        lines = transaction.pop('lines')
        last_string_index = self.get_last_string_index(lines)
        transaction['TransactionType'] = lines[0]
        transaction['Description'] = lines[1]
        if transaction['Description'] in self.holdings:
            transaction['Symbol'] = self.holdings[transaction['Description']]['symbol']
            transaction['SecurityType'] = self.holdings[transaction['Description']]['type']
        transaction['Comments'] = ' '.join(lines[2:(last_string_index+1)])
        # NOTE: this is a hack
        if transaction['Description'] == 'UNITED STATES TREASURY BILL':
            cusip = transaction['Comments'].split(' [')[1].split(']')[0]
            transaction['Description'] += ' ' + cusip
            transaction['Symbol'] = cusip
            transaction['SecurityType'] = 'TREASURY BILL'
        transaction['Amount'] = self.get_float(lines[-1])
        if last_string_index < -2:
            transaction['Quantity'] = self.get_float(lines[last_string_index+1])
            if transaction['TransactionType'] in ['Bought', 'Sold', 'Redemption']:
                transaction['Quantity'] *= -math.copysign(1, transaction['Amount'])
        if last_string_index < -3:
            transaction['Price'] = self.get_float(lines[last_string_index+2])
            if transaction['TransactionType'] in ['Redemption']:
                transaction['Price'] /= 100

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

