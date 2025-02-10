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

        self.__set_account_info()
        self.__set_transactions()

        print('Account Number: %s' % self.account_number)
        print('Account Type  : %s' % self.account_type)
        print('Start Date    : %s' % self.start_date)
        print('End Date      : %s' % self.end_date)

        pp(self.transactions)

    def test(self):
        self.__set_name_pages()
        for page_num in self.__name_pages['Account Number']['pages']:
            for line in self.statement.get_page_lines(page_num):
                if line.startswith('SECURITIES PURCHASED OR SOLD (MUTUAL FUND ACTIVITY LISTED IN SEPARATE SECTION)'):
                    print('\t%s' % line)

    def __set_account_info(self):
        self.__set_name_pages()
        self.account_type = None
        self.start_number = None
        self.account_name = None
        self.end_date = None
        
        page_num = self.__name_pages['Account Number']['pages'][0]
        for block in self.statement.get_page_blocks(page_num):
            if block[0].startswith('Account Number:'):
                self.account_number = block[0].split(':')[-1].strip()
                self.account_type = block[2].split(':')[-1].strip()
                date = block[1].split(':')[-1].strip()
                date = date.split('-')
                self.start_date = datetime.strptime(date[0].strip(), '%B %d, %Y')
                self.end_date = datetime.strptime(date[1].strip(), '%B %d, %Y')
        
    def __set_transactions(self):
        self.transactions = []

        # TODO: Maybe pop lines after using them ?

        account_number = self.__name_pages['Account Number']['children']
        for page_name, page_data in account_number.items():
            if len(page_data['lines']) > 0:
                self.__get_transactions(page_data['lines'], page_name)

    def __get_transactions(self, lines, page_name):
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
                        self.__parse_transaction(current_transaction, page_name)
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
            self.__parse_transaction(current_transaction, page_name)
            self.transactions.append(current_transaction)

    def __parse_transaction(self, transaction, page_name):
        self.__trim_transaction_lines(transaction)
        lines = transaction.pop('lines')
        last_string_index = self.__get_last_string_index(lines)
        
        if page_name in [
            'SECURITIES PURCHASED OR SOLD',
            'SECURITIES PURCHASED OR SOLD (MUTUAL FUND ACTIVITY LISTED IN SEPARATE SECTION)',
            'MUTUAL FUNDS PURCHASED OR SOLD',
            ]:
            transaction['TransactionType'] = lines[last_string_index]
            transaction['Description'] = ' '.join(lines[0:(last_string_index-1)])
            transaction['Symbol'] = lines[last_string_index-1]
            transaction['Quantity'] = self.__get_float(lines[last_string_index+1])
            transaction['Price'] = self.__get_float(lines[last_string_index+2])
            transaction['Amount'] = self.__get_float(lines[-1])
            if transaction['TransactionType'] == 'Bought':
                transaction['Amount'] *= -math.copysign(1, transaction['Quantity'])

        if page_name in [
            'DIVIDENDS & INTEREST ACTIVITY',
            'CONTRIBUTIONS & DISTRIBUTIONS ACTIVITY', 
            'WITHDRAWALS & DEPOSITS',
            ]:
            transaction['TransactionType'] = lines[0]
            transaction['Amount'] = self.__get_float(lines[-1])
            
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

        if page_name in ['OTHER ACTIVITY']:
            if lines[last_string_index] in ['Conversion', 'Dividend', 'Other']:
                transaction['TransactionType'] = lines[last_string_index]
                transaction['Description'] = ' '.join(lines[0:(last_string_index-1)])
                transaction['Symbol'] = lines[last_string_index-1]
                transaction['Amount'] = self.__get_float(lines[-1])

                # pp(transaction, etrade_log)

            if lines[last_string_index] in ['Redemption', 'Reinvest', 'Conversion']:
                transaction['TransactionType'] = lines[last_string_index]
                transaction['Description'] = ' '.join(lines[0:(last_string_index-1)])
                transaction['Symbol'] = lines[last_string_index-1]
                transaction['Quantity'] = self.__get_float(lines[last_string_index+1])
                transaction['Amount'] = self.__get_float(lines[-2])
                if transaction['TransactionType'] == 'Reinvest':
                    transaction['Amount'] *= -math.copysign(1, transaction['Quantity'])

    def __trim_transaction_lines(self, transaction):
        index = 0
        for line in transaction['lines']:
            if 'PAGE ' in line and ' OF ' in line:
                transaction['lines'] = transaction['lines'][:index]
                return
            index += 1

    def __get_float(self, text):
        if text.startswith('$'): text = text[1:]
        if text.startswith('('): text = '-'+text[1:-1]
        text = text.replace(',', '')
        try:
            return float(text)
        except:
            return None

    def __get_last_string_index(self, lines):
            index = 1
            lines_reverse = lines.copy()
            lines_reverse.reverse()
            for line in lines_reverse:
                if self.__get_float(line) == None: break
                index += 1
            index = -index
            return index

    def __set_name_pages(self):
        self.__name_pages = {
            'Account Number': {
                'pages': [],
                'children': {
                    'SECURITIES PURCHASED OR SOLD': {
                        'stop': 'TOTAL SECURITIES ACTIVITY',
                        'lines': [],
                    },
                    'SECURITIES PURCHASED OR SOLD (MUTUAL FUND ACTIVITY LISTED IN SEPARATE SECTION)': {
                        'stop': 'TOTAL SECURITIES ACTIVITY',
                        'lines': [],
                    },
                    'MUTUAL FUNDS PURCHASED OR SOLD': {
                        'stop': 'TOTAL MUTUAL FUNDS ACTIVITY',
                        'lines': [],
                    },
                    'DIVIDENDS & INTEREST ACTIVITY': {
                        'stop': 'TOTAL DIVIDENDS & INTEREST ACTIVITY',
                        'lines': [],
                    },
                    'CONTRIBUTIONS & DISTRIBUTIONS ACTIVITY': {
                        'stop': 'TOTAL CONTRIBUTIONS & DISTRIBUTIONS',
                        'lines': [],
                    },
                    'WITHDRAWALS & DEPOSITS': {
                        'stop': 'NET WITHDRAWALS & DEPOSITS',
                        'lines': [],
                    },
                    'OTHER ACTIVITY': {
                        'stop': 'TOTAL OTHER ACTIVITY',
                        'lines': [],
                    },
                },
            },
        }
        for page_num, blocks in self.statement.get_blocks().items():
            for block in blocks:
                # print('%s: %s' % (block[0], page_num))
                for page_name in self.__name_pages.keys():
                    if block[0].startswith(page_name):
                        # print('%s: %s' % (block[0], page_num))
                        self.__name_pages[page_name]['pages'].append(page_num)
                        break
        for page_name, page_data in self.__name_pages.items():
            if len(page_data['pages']) > 0:
                if len(page_data['children']) > 0:
                    lines = []
                    for page_num in page_data['pages']:
                        blocks = self.statement.get_page_blocks(page_num)
                        for block in blocks:
                            lines += block
                    self.recurse_lines(page_data['children'], lines)

    def recurse_lines(self, name_pages, lines):
        current_name = None
        for line in lines:
            
            if current_name != None:
                if 'stop' in name_pages[current_name]:
                    if line == name_pages[current_name]['stop']:
                        current_name = None
                        continue
            
            if line in name_pages.keys():
                current_name = line
                continue

            if current_name != None:
                name_pages[current_name]['lines'].append(line)

        for name, name_data in name_pages.items():
            if 'children' in name_data:
                self.recurse_lines(name_data['children'], name_data['lines'])
