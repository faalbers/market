from datetime import datetime, timedelta
from pprint import pp
import math, copy
import pandas as pd

class Scottrade_V2():
    name = 'Scottrade_V2'

    def __init__(self, statement):
        self.statement = statement
        self.accounts = {}

        # if self.statement.pdf_file != 'database/statements_st\\STRO_2010-02.pdf': return
        # if self.statement.pdf_file != 'database/statements_st\\ST-Roth_06-09.pdf': return
        # if self.statement.pdf_file != 'database/statements_st\\STRO_2006_04.pdf': return
        # if self.statement.pdf_file != 'database/statements_st\\ST-Roth_05-11.pdf': return
        
        # return

        # print()
        # print('%s: %s' % (self.name, self.statement.pdf_file))

        self.__set_name_pages()
        self.__set_accounts_info()
        self.__set_holdings()
        self.__set_transactions()

        # pp(self.accounts)
        # if self.statement.pdf_file == 'database/statements_st\\ST-Roth_05-01.pdf':
        #     pp(self.accounts)

    def __set_transactions(self):
        for account_number, account_data in self.__name_pages['accounts'].items():
            # print(account_number)
            
            children = account_data['Account']['children']
            
            lines = children['ACCOUNT ACTIVITY']['lines']
            if len(lines) > 0:
                # print('\t%s' % 'ACCOUNT ACTIVITY')
                self.__get_transactions(lines, account_number)

    def __get_transactions(self, lines, account_number):
        account = self.accounts[account_number]

        current_transaction = {}
        for line_index in range(len(lines)):
            line = lines[line_index]
            
            # handle double lines in earlier versions
            line_splits = line.split(' ')
            double_line = False
            if len(line_splits) > 1:
                line_0 = line_splits[0].strip()
                line_1 = ' '.join(line_splits[1:]).strip()
                line_digits = line_0.replace('/', '')
                is_date_line = line_digits.isdigit() and line_0 != line_digits and len(line_digits) == 6
                double_line = True
            else:
                line_digits = line.replace('/', '')
                is_date_line = line_digits.isdigit() and line != line_digits and len(line_digits) == 6
            
            if is_date_line:
                # print(line)
                # create a datetime object from the date line
                if double_line:
                    date = datetime.strptime(line_0, '%m/%d/%y')
                else:
                    date = datetime.strptime(line, '%m/%d/%y')

                if 'transaction_date' in current_transaction:
                    self.__parse_transaction(current_transaction, account_number)
                    self.__add_transaction(current_transaction, account_number)
                
                if double_line:
                    current_transaction = {'transaction_date': date, 'lines': [line_1]}
                else:
                    current_transaction = {'transaction_date': date, 'lines': []}

            elif 'transaction_date' in current_transaction:
                current_transaction['lines'].append(line)

        # make sure the last transaction is added if needed
        if 'transaction_date' in current_transaction:
            self.__parse_transaction(current_transaction, account_number)
            self.__add_transaction(current_transaction, account_number)

    def __add_transaction(self, transaction, account_number):
        account = self.accounts[account_number]
        if not 'type' in transaction: return
        security = transaction.pop('security')
        symbol = transaction.pop('symbol')

        if security in account['holdings']:
            account['holdings'][security]['transactions'].append(transaction)
        else:
            account['holdings'][security] = {'type': None, 'symbol': symbol, 'cusip': None, 'date': account['end_date'], 'transactions': []}
            account['holdings'][security]['transactions'].append(transaction)

    def __parse_transaction(self, transaction, account_number):
        lines = transaction.pop('lines')
        lines = self.__trim_account_lines(lines)

        if lines[0] in ['CREDIT INTEREST']: return
        # pp(transaction)

        # find security index
        security_idx = None
        for account_number, account_data in self.accounts.items():
            for security in account_data['holdings']:
                if security in lines:
                    security_idx = lines.index(security)
                    break
                for line_idx in range(len(lines)):
                    line = lines[line_idx]
                    if line.startswith(security):
                        security_idx = lines.index(line)
                        break
                if security_idx != None: break
        
        if security_idx == None:
            # security not found
            # HACK hard coded
            if lines[0].strip() == 'SOLD':
                transaction['type'] = 'SOLD'
                transaction['quantity'] = -self.__get_float(lines[1])
                transaction['security'] = lines[2].replace('*STK','').strip() 
                transaction['comments'] = lines[3].strip()
                transaction['price'] = self.__get_float(lines[4])
                transaction['amount'] = self.__get_float(lines[5])
            elif lines[0].strip() == 'DELIVER':
                transaction['type'] = 'DELIVER SECURITIES'
                transaction['quantity'] = -self.__get_float(lines[2])
                transaction['security'] = lines[3].replace('*STK','').strip() 
                transaction['comments'] = lines[4].strip()
                transaction['amount'] = self.__get_float(lines[5])
            elif lines[0].strip() == 'TAXABLE DIVIDEND':
                transaction['type'] = 'TAXABLE DIVIDEND'
                transaction['security'] = lines[1].replace('*STK','').strip() 
                transaction['comments'] = lines[2].strip()
                transaction['amount'] = self.__get_float(lines[3])
            else:
                transaction['type'] = lines[0].strip()
                transaction['quantity'] = self.__get_float(lines[1])
                transaction['security'] = lines[2].replace('*STK','').strip() 
                transaction['comments'] = lines[3].strip()
                transaction['amount'] = self.__get_float(lines[4])
        else:
            transaction['security'] = lines[security_idx].replace('*STK','').strip()
            transaction['comments'] = lines[security_idx+1].strip()
            transaction['quantity'] = self.__get_float(lines[security_idx-1])
            if transaction['quantity'] == None:
                transaction['type'] = ' '.join(lines[:security_idx])
            else:
                transaction['type'] = ' '.join(lines[:security_idx-1])
            values = []
            if transaction['type'] in ['SOLD', 'DELIVER SECURITIES']:
                transaction['quantity'] = -transaction['quantity']
            for line in lines[security_idx+2:]:
                value = self.__get_float(line)
                if value == None: break
                values.append(value)
            if len(values) > 2:
                if transaction['type'] in ['TAXABLE DIVIDEND', 'CASH IN LIEU']:
                    transaction['amount'] = values[0]
                else:
                    transaction['price'] = values[0]
                    transaction['amount'] = values[1]
            else:
                transaction['amount'] = values[0]

        transaction['symbol'] = transaction['comments'].split(' ')[-1].strip()
        if transaction['symbol'][0] == '$':
            transaction['symbol'] = transaction['symbol'][-5:]
        transaction['symbol'] = transaction['symbol'].replace('Rece','').strip()
        transaction['symbol'] = transaction['symbol'].replace('Sh','').strip()
        if transaction['symbol'] == 'SBC': transaction['symbol'] = 'T'
        if transaction['symbol'] == 'T':
            transaction['security'] = 'AT&T INC'


    def __trim_account_lines(self, lines):
        trim_lines = ['12855 Flushing Meadow P.O. Box 31759', 'P.O. Box 31759']
        for trim_line in trim_lines:
            if trim_line in lines:
                return lines[:lines.index(trim_line)]
        return lines

    def __set_holdings(self):
        for account_number, account_data in self.__name_pages['accounts'].items():
            # print('%s' % account_number)
            children = account_data['Account']['children']

            lines = children['SECURITY POSITIONS']['lines']
            if len(lines) > 0:
                # print('\tSECURITY POSITIONS')
                self.__add_stock(lines, account_number)

    def __add_stock(self, lines, account_number):
        account = self.accounts[account_number]

        # lines = lines[lines.index('Cur. Yld')+1:]
        lines = lines[lines.index('Cur.Yld.')+1:]
 
        for line_idx in range(len(lines)):
            line = lines[line_idx]
            if not line in ['CASH', 'MARGIN']: continue
            stock_lines = lines[line_idx+1:]
            splits = stock_lines[0].split(' ')
            if len(splits) > 1:
                stock_lines = [splits[0]] + [splits[-1]] + stock_lines[1:]

            symbol = stock_lines[0]
            if symbol == 'SBC':
                symbol = 'T'
            if symbol.endswith('XX'):
                security_type = 'money market fund'
            elif symbol.endswith('X'):
                security_type = 'mutual fund'
            else:
                security_type = 'stock'

            quantity = self.__get_float(stock_lines[1])
            if symbol == 'T':
                security = 'AT&T INC'
            else:
                security = stock_lines[2]
                if security.endswith('*STK'): security = security[:-4].strip()

            if not security in account['holdings']:
                account['holdings'][security] = {
                    'type': security_type, 'symbol': symbol, 'cusip': None, 'date': account['end_date'], 'quantity': quantity, 'transactions': []}
            else:
                account['holdings'][security]['quantity'] += quantity

    def __get_float(self, text):
        text = text.replace('$', '')
        text = text.replace(',', '')
        text = text.replace(' ', '')
        try:
            return float(text)
        except:
            return None

    def __set_accounts_info(self):
        for account_number, account_data in self.__name_pages['accounts'].items():
            self.accounts[account_number] = {'statement': self.statement.pdf_file, 'holdings': {}, 'type': None}
            page_num = account_data['Account']['pages'][0]
            # if len(account_data['Account']['pages']) > 1:
            #     print('%s: %s' % (self.name, self.statement.pdf_file))
            blocks = self.statement.get_page_blocks(page_num)
            for block_idx in range(len(blocks)):
                block = blocks[block_idx]

                if block[0] == 'Period Ending':
                    self.accounts[account_number]['start_date'] = datetime.strptime(block[3].strip(), '%B %d, %Y') + timedelta(days=1)
                    self.accounts[account_number]['end_date'] = datetime.strptime(block[2].strip(), '%B %d, %Y')
                    break
                
                # if block[0] == 'Account Number' and len(block) > 4:
                if block[0] == 'Account Number':
                    self.accounts[account_number]['start_date'] = datetime.strptime(block[7].strip(), '%B %d, %Y') + timedelta(days=1)
                    self.accounts[account_number]['end_date'] = datetime.strptime(block[6].strip(), '%B %d, %Y')
                    break

    def __set_name_pages(self):
        keywords = [
            'BANK DEPOSIT ACTIVITY',
            'CASH ACCOUNT ACTIVITY',
            'MARGIN ACCOUNT ACTIVITY',
            'SECURITY POSITIONS',
            'TRADES PENDING SETTLEMENT',
        ]
        self.__name_pages = {
            'accounts': {},
            'Account': {
                'pages': [],
                'children': {
                    # holdings
                    'SECURITY POSITIONS': {
                        'stop': 'TOTAL',
                        'lines': [],
                    },
                    
                    # Activity
                    'ACCOUNT ACTIVITY': {
                        'stop': 'CLOSING BALANCE',
                        'lines': [],
                    },
                },
            },
        }

        # search first page for 'Account Number'
        blocks = self.statement.get_page_blocks(0)
        for block_idx in range(len(blocks)):
            block = blocks[block_idx]
            if block[0] == 'Account Number':
                account_number = block[2].strip()
                self.__name_pages['accounts'][account_number] = {}
                self.__name_pages['accounts'][account_number]['Account'] = copy.deepcopy(self.__name_pages['Account'])
                self.__name_pages['accounts'][account_number]['Account']['pages'] = list(range(self.statement.page_count))
                break

        for account_number, account_data in self.__name_pages['accounts'].items():
            for pages_name, page_data in account_data.items():
                if len(page_data['pages']) > 0:
                    if len(page_data['children']) > 0:
                        lines = []
                        for page_num in page_data['pages']:
                            blocks = self.statement.get_page_blocks(page_num)
                            for block in blocks:
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
                # since they have no (continued) in the name
                if current_name == line: continue
                # print('start: new: %s - old: %s' % (line, current_name))
                current_name = line
                current_lines = []
                continue

            if current_name != None:
                current_lines.append(line)
        
        if current_name != None:
            name_pages[current_name]['lines'] = current_lines
            raise Exception('last current name not stopped: %s' % current_name)
            # print('%s: %s' % (self.name, self.statement.pdf_file))
            # print(current_name)
            # for line in current_lines:
            #     print('\t%s' % line)

        for name, name_data in name_pages.items():
            if 'children' in name_data:
                self.__recurse_lines(name_data['children'], name_data['lines'])
