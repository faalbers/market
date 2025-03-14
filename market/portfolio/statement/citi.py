from datetime import datetime
from pprint import pp
import math, copy
import pandas as pd

class Citi():
    name = 'Citi'

    def __init__(self, statement):
        self.statement = statement
        self.accounts = {}

        # if self.statement.pdf_file != 'database/statements_ms\\240-26077-13_2012_04-06.pdf': return

        return

        print('')
        print('%s: %s' % (self.name, self.statement.pdf_file))

        self.__set_name_pages()
        self.__set_accounts_info()
        self.__set_holdings()
        self.__set_transactions()

        # pp(self.__name_pages['accounts'])
        # pp(self.accounts)

    def __set_transactions(self):
        for account_number, account_data in self.__name_pages['accounts'].items():
            # print(account_number)
            
            children = account_data['Account number']['children']
            
            activities = [
                'Other security activity',
                'Qualified dividends',
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
            if line_digits.isdigit() and line != line_digits and len(line_digits) == 6:
                # create a datetime object from the date line
                date_elements = line.split('/')
                date = datetime.strptime(line, '%m/%d/%y')

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
        security = transaction.pop('security')

        if security in account['holdings']:
            account['holdings'][security]['transactions'].append(transaction)
        else:
            # HACK just for when it's not in holdings anymore
            if security == 'WALT DISNEY CO':
                type = 'stock'
                symbol = 'DIS'
                cusip = None
            account['holdings'][security] = {'type': type, 'symbol': symbol, 'cusip': cusip, 'date': account['end_date'], 'transactions': []}
            account['holdings'][security]['transactions'].append(transaction)

    def __parse_transaction(self, transaction, activity):
        lines = transaction.pop('lines')
        if activity == 'Other security activity':
            transaction['type'] = lines[0].strip()
            transaction['security'] = lines[3].strip()
            transaction['comments'] = lines[4].strip()
            transaction['quantity'] = self.__get_float(lines[1].strip())
            transaction['amount'] = self.__get_float(lines[2].strip())
        elif activity == 'Qualified dividends':
            transaction['type'] = 'Qualified dividend'
            transaction['security'] = lines[2].strip()
            transaction['comments'] = lines[3].strip()
            transaction['amount'] = self.__get_float(lines[0].strip())

        # pp(transaction)

    def __get_float(self, text):
        if text.startswith('$'): text = text[1:]
        if text.startswith('('): text = '-'+text[1:-1]
        text = text.replace(',', '')
        try:
            return float(text)
        except:
            return None

    def __set_holdings(self):
        for account_number, account_data in self.__name_pages['accounts'].items():
            # print('%s' % account_number)
            children = account_data['Account number']['children']

            lines = children['Common stocks & options']['lines']
            if len(lines) > 0:
                # print('\tCommon stocks & options')
                self.__add_stock(lines, account_number)

    def __add_stock(self, lines, account_number):
        # add core data to account holdings
        account = self.accounts[account_number]

        lines = lines[lines.index('(annualized)')+1:]
        
        security = lines[0].strip()
        symbol = lines[1].strip()
        quantity = self.__get_float(lines[-7].strip())
        account['holdings'][security] = {
            'type': 'stock', 'symbol': symbol, 'cusip': None, 'date': account['end_date'], 'transactions': [],
            'quantity': quantity}

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
                page_num = account_data['Account number']['pages'][0]
                for block in self.statement.get_page_blocks(page_num):
                    if block[0] == 'Client Statement':
                        date_string = block[1].strip()
                        break
        dates = date_string.split(' - ')
        year = dates[1].split(',')[1].strip()
        start_date = dates[0].strip() + ', ' + year
        start_date = datetime.strptime(start_date, '%B %d, %Y')
        end_date = dates[1].strip()
        end_date = datetime.strptime(end_date, '%B %d, %Y')
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
            'Account number': {
                'pages': [],
                'children': {
                    # Holdings
                    'Common stocks & options': {
                        'stop': 'Total common stocks and options',
                        'lines': [],
                    },

                    # Activity
                    'Other security activity': {
                        'stop': 'Net value of securities deposited/(withdrawn) + capital contributions',
                        'lines': [],
                    },
                    'Qualified dividends': {
                        'stop': 'Total qualified dividends earned',
                        'lines': [],
                    },

                },
            },
        }

        for page_num, blocks in self.statement.get_blocks().items():
            for block_idx in range(len(blocks)):
                block = blocks[block_idx]
                if block[0].startswith('Account number'):
                    account_number = block[0].split('Account number')[1].strip()
                    if account_number not in self.__name_pages['accounts']:
                        self.__name_pages['accounts'][account_number] = {}
                        self.__name_pages['accounts'][account_number]['Account number'] = copy.deepcopy(self.__name_pages['Account number'])
                    self.__name_pages['accounts'][account_number]['Account number']['pages'].append(page_num)
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
                                #     if line in ['TRANSACTION DETAILS', 'EARNINGS DETAILS']:
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
                # print('start: new: %s - old: %s' % (line, current_name))
                current_name = line
                current_lines = []
                continue

            if current_name != None:
                current_lines.append(line)
        
        if current_name != None:
            pass
            # raise Exception('last current name not stopped: %s' % current_name)
            # print('%s: %s' % (self.name, self.statement.pdf_file))
            # print(current_name)
            # for line in current_lines:
            #     print('\t%s' % line)

        for name, name_data in name_pages.items():
            if 'children' in name_data:
                self.__recurse_lines(name_data['children'], name_data['lines'])
