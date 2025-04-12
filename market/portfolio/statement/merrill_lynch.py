from datetime import datetime
from pprint import pp
import math, copy
import pandas as pd

class Merrill_Lynch():
    name = 'Merrill_Lynch'

    def __init__(self, statement):
        self.statement = statement
        self.accounts = {}

        # TODO statement below gives empty account number
        # if self.statement.pdf_file != 'database/statements_ml\\7WA 15527-2012-01-03.pdf': return

        # return

        # print('')
        # print('%s: %s' % (self.name, self.statement.pdf_file))

        self.__set_name_pages()
        self.__set_accounts_info()
        self.__set_holdings()
        self.__set_transactions()

        # pp(self.__name_pages['accounts'])
        # pp(self.accounts)
        # if self.statement.pdf_file == 'database/statements_ml\\7WA 15527-2011-10-12.pdf':
        #     pp(self.accounts)
        # if self.statement.pdf_file == 'database/statements_ml\\7WA 15527-2012-01-03.pdf':
        #     pp(self.accounts)

    def __set_transactions(self):
        for account_number, account_data in self.__name_pages['accounts'].items():
            # print(account_number)
            
            children = account_data['Account']['children']
            
            activities = [
                'DIVIDENDS/INTEREST INCOME TRANSACTIONS',
                'DIVIDENDS/INTEREST',
                'SECURITY TRANSACTIONS',
                'SECURITIES YOU TRANSFERRED IN/OUT',
                'SECURITIES',
            ]

            for activity in activities:
                lines = children[activity]['lines']
                if len(lines) > 0:
                    # print('\t%s' % activity)
                    self.__get_transactions(lines, account_number, activity)

    def __get_transactions(self, lines, account_number, activity):
        account = self.accounts[account_number]
        current_transaction = {}
        for line_index in range(len(lines)):
            line = lines[line_index]
            line_digits = line.replace('/', '')
            if line_digits.isdigit() and line != line_digits and len(line_digits) <= 4:
                # create a datetime object from the date line
                date_elements = line.split('/')
                date = datetime(month=int(date_elements[0]), day=int(date_elements[1]), year=account['end_date'].year)

                if 'transaction_date' in current_transaction:
                    self.__parse_transaction(current_transaction, activity)
                    self.__add_transaction(current_transaction, account_number)
                
                current_transaction = {'transaction_date': date, 'lines': []}

            elif 'transaction_date' in current_transaction:
                current_transaction['lines'].append(line)
        
        # make sure the last transaction is added if needed
        if 'transaction_date' in current_transaction:
            self.__parse_transaction(current_transaction, activity)
            self.__add_transaction(current_transaction, account_number)

    def __add_transaction(self, transaction, account_number):
        account = self.accounts[account_number]
        if not 'type' in transaction: return
        security = transaction.pop('security')
        account['holdings'][security]['transactions'].append(transaction)

    def __parse_transaction(self, transaction, activity):
        lines = transaction.pop('lines')
        quantity = None
        price = None
        amount = None
        if activity == 'DIVIDENDS/INTEREST INCOME TRANSACTIONS':
            start_idex = 0
            if lines[0] == '*': start_idex = 1
            transaction_type = lines[start_idex].replace('*', '').strip()
            security = lines[start_idex+1].strip()
            amount = self.__get_float(lines[start_idex+2].strip())
        elif activity == 'DIVIDENDS/INTEREST':
            start_idex = 0
            if lines[0] == '*': start_idex = 1
            transaction_type = lines[start_idex].replace('*', '').strip()
            security = lines[start_idex+1].strip()
            amount = self.__get_float(lines[start_idex+2].strip())
        elif activity == 'SECURITY TRANSACTIONS':
            transaction_type = lines[1].replace('*', '').strip()
            security = lines[0].strip()
            quantity = self.__get_float(lines[2].strip())
            price = self.__get_float(lines[3].strip())
        elif activity in ['SECURITIES YOU TRANSFERRED IN/OUT', 'SECURITIES']:
            transaction_type = lines[1].replace('*', '').strip()
            security = lines[0].strip()
            quantity = self.__get_float(lines[2].strip())
            transaction['value'] = self.__get_float(lines[3].strip())
        transaction['type'] = transaction_type
        transaction['security'] = security
        transaction['quantity'] = quantity
        transaction['price'] = price
        transaction['amount'] = amount

        # pp(transaction)

    def __set_holdings(self):
        for account_number, account_data in self.__name_pages['accounts'].items():
            # print('%s' % account_number)
            children = account_data['Account']['children']

            lines = children['EQUITIES']['lines']
            if len(lines) > 0:
                # print('\tEQUITIES')
                self.__add_stock(lines, account_number)

    def __add_stock(self, lines, account_number):
        # add core data to account holdings
        account = self.accounts[account_number]

        # not even parsing since it's always only one
        lines = lines[lines.index('Yield%')+1:]
        security = lines[0].strip()
        symbol = lines[1].strip()
        if 'Subtotal' in lines:
            quantity = self.__get_float(lines[lines.index('Subtotal')+1])
        else:
            quantity = self.__get_float(lines[3].strip())
        account['holdings'][security] = {
            'type': 'stock', 'symbol': symbol, 'cusip': None, 'date': account['end_date'], 'quantity': quantity, 'transactions': []}

    def __get_float(self, text):
        text = text.replace('$', '')
        text = text.replace(',', '')
        try:
            return float(text)
        except:
            return None

    def __set_accounts_info(self):
        date_string = None
        for account_number, account_data in self.__name_pages['accounts'].items():
            self.accounts[account_number] = {'type': 'INDIVIDUAL INVESTOR ACCOUNT', 'statement': self.statement.pdf_file, 'holdings': {}}
            if date_string == None:
                page_num = account_data['Account']['pages'][0]
                for block in self.statement.get_page_blocks(page_num):
                    if block[0].startswith('INDIVIDUAL INVESTOR ACCOUNT') and ' - ' in block[1]:
                        date_string = block[1].strip()
                        break
                    if ' - ' in block[0]:
                        date_string = block[0].strip()
                        break
                    if len(block) > 1 and block[1].startswith('- '):
                        date_string = ' '.join(block[:2]).strip()
                        break
        dates = date_string.split(' - ')
        start_date = datetime.strptime(dates[0].strip(), '%B %d, %Y')
        end_date = datetime.strptime(dates[1].strip(), '%B %d, %Y')
        for account_number, account_data in self.accounts.items():
            account_data['start_date'] = start_date
            account_data['end_date'] = end_date

    def __set_name_pages(self):
        # search structure:
        # key words under children are the start key words of blocks of lines
        # the 'stop' keyword is the end key word of blocks of those lines
        # the 'lines' feyword has all the lines of that block
        self.__name_pages = {
            'accounts': {},
            'Account': {
                'pages': [],
                'children': {
                    # Holdings
                    'EQUITIES': {
                        'stop': 'TOTAL',
                        'lines': [],
                    },

                    # Activity
                    'DIVIDENDS/INTEREST INCOME TRANSACTIONS': {
                        'stop': 'NET TOTAL',
                        'lines': [],
                    },
                    'DIVIDENDS/INTEREST': {
                        'stop': 'NET',
                        'lines': [],
                    },
                    'SECURITY TRANSACTIONS': {
                        'stop': 'TOTAL',
                        'lines': [],
                    },
                    'SECURITIES YOU TRANSFERRED IN/OUT': {
                        'stop': 'NET TOTAL',
                        'lines': [],
                    },
                    'SECURITIES': {
                        'stop': 'NET',
                        'lines': [],
                    },
                },
            },
        }

        for page_num, blocks in self.statement.get_blocks().items():
            for block_idx in range(len(blocks)):
                block = blocks[block_idx]
                for line in block:
                    if line.startswith('Account Number:'):
                        account_number = line
                        if len(account_number) <= 15:
                            account_number_idx = block.index(line)
                            account_number = ' '.join(block[account_number_idx:account_number_idx+2])
                        account_number = account_number.split(':')[1].strip()
                        if account_number not in self.__name_pages['accounts']:
                            self.__name_pages['accounts'][account_number] = {}
                            self.__name_pages['accounts'][account_number]['Account'] = copy.deepcopy(self.__name_pages['Account'])
                        self.__name_pages['accounts'][account_number]['Account']['pages'].append(page_num)
                        break

        for account_number, account_data in self.__name_pages['accounts'].items():
            for pages_name, page_data in account_data.items():
                if len(page_data['pages']) > 0:
                    if len(page_data['children']) > 0:
                        lines = []
                        for page_num in page_data['pages']:
                            blocks = self.statement.get_page_blocks(page_num)
                            for block in blocks:
                                # for line in block:
                                #     # if 'Contin' in line or 'contin' in line or 'CONTIN' in line:
                                #     if '(continued)' in line:
                                #         print(line)
                                #         print('\t%s' % self.statement.pdf_file)
                                lines += block
                        self.__recurse_lines(page_data['children'], lines)

    def __recurse_lines(self, name_pages, lines):
        current_name = None
        current_lines = []
        for line in lines:
            if current_name != None:
                if 'stop' in name_pages[current_name]:
                    if line == name_pages[current_name]['stop']:
                        # print('stop: %s - with: %s' % (current_name, line))
                        name_pages[current_name]['lines'] = current_lines
                        current_name = None
                        current_lines = []
                        continue
            
            if line in name_pages:
                if current_name != None:
                    continue
                    # print('%s: %s' % (self.name, self.statement.pdf_file))
                    # print('not stopped: %s before start of: %s' % (current_name, key))
                # print('start: new: %s - old: %s' % (line, current_name))
                current_name = line
                current_lines = []
                continue

            if current_name != None:
                current_lines.append(line)
        
        if current_name != None:
            pass
            # print('last current name not stopped: %s' % current_name)
            # print('stop: %s - with: %s' % (current_name, line))
            # name_pages[current_name]['lines'] = current_lines
            # raise Exception('last current name not stopped: %s' % current_name)
            # print('%s: %s' % (self.name, self.statement.pdf_file))
            # print(current_name)
            # for line in current_lines:
            #     print('\t%s' % line)

        for name, name_data in name_pages.items():
            if 'children' in name_data:
                self.__recurse_lines(name_data['children'], name_data['lines'])
