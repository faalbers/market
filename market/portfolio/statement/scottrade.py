from datetime import datetime
from pprint import pp
import math, copy
import pandas as pd

class Scottrade():
    name = 'Scottrade'

    def __init__(self, statement):
        self.statement = statement
        self.accounts = {}

        # if self.statement.pdf_file != 'database/statements_st\\STRO_2013-12.pdf': return
        
        return

        # print('')
        # print('%s: %s' % (self.name, self.statement.pdf_file))

        self.__set_name_pages()
        self.__set_accounts_info()
        self.__set_holdings()
        self.__set_transactions()

        # pp(self.__name_pages['accounts'])
        # pp(self.accounts)

    def __set_transactions(self):
        for account_number, account_data in self.__name_pages['accounts'].items():
            # print(account_number)
            
            children = account_data['Account']['children']
            
            activities = [
                'CASH ACCOUNT ACTIVITY',
                'MARGIN ACCOUNT ACTIVITY',
                'TRADES PENDING SETTLEMENT',
            ]

            for activity in activities:
                lines = children[activity]['lines']
                if len(lines) > 0:
                    # print('\t%s' % activity)
                    self.__get_transactions(lines, account_number, activity)

    def __get_transactions(self, lines, account_number, activity):
        account = self.accounts[account_number]

        if lines[0] == 'Type': version = 3
        elif lines[2] == 'Quantity': version = 1
        elif lines[2] == 'Symbol / Cusip': version = 2
        # elif lines[2] == 'Description': version = 3
        else: raise Exception('unknown version: %s' % lines[2])

        current_transaction = {}
        for line_index in range(len(lines)):
            line = lines[line_index]
            line_digits = line.replace('/', '')
            if line_digits.isdigit() and line != line_digits and len(line_digits) == 6:
                # create a datetime object from the date line
                date_elements = line.split('/')
                date = datetime.strptime(line, '%m/%d/%y')

                if 'transaction_date' in current_transaction:
                    self.__parse_transaction(current_transaction, account_number, version, activity)
                    self.__add_transaction(current_transaction, account_number)
                
                current_transaction = {'transaction_date': date, 'lines': []}

            elif 'transaction_date' in current_transaction:
                current_transaction['lines'].append(line)
        
        # make sure the last transaction is added if needed
        if 'transaction_date' in current_transaction:
            self.__parse_transaction(current_transaction, account_number, version, activity)
            self.__add_transaction(current_transaction, account_number)

    def __add_transaction(self, transaction, account_number):
        account = self.accounts[account_number]
        if not 'type' in transaction: return
        security = transaction.pop('security')
        symbol = transaction.pop('symbol')
        cusip = transaction.pop('cusip')

        if security in account['holdings']:
            account['holdings'][security]['transactions'].append(transaction)
        else:
            account['holdings'][security] = {'type': None, 'symbol': symbol, 'cusip': cusip, 'date': account['end_date'], 'transactions': []}
            account['holdings'][security]['transactions'].append(transaction)

    def __parse_transaction(self, transaction, account_number, version, activity):
        lines = transaction.pop('lines')
        lines = self.__trim_account_lines(lines, account_number)

        # version 1: Date Transaction Quantity Description Price Amount Balance
        # version 2: Date Transaction Symbol/Cusip Quantity TaxLotMethod** Description Price Amount Balance
        
        if version == 1:
            quantity_idx = 1
            if lines[quantity_idx] in ['SECURITIES', 'GAIN']: quantity_idx = 2
            transaction_type = ' '.join(lines[0:quantity_idx]).strip()
            if transaction_type in ['CREDIT INTEREST', 'ADJUSTMENT']: return
            
            quantity = self.__get_float(lines[quantity_idx].strip())
            if quantity != None: description_start_idx = quantity_idx+1
            else: description_start_idx = quantity_idx

            if transaction_type in ['DELIVER SECURITIES', 'RECEIVE SECURITIES']:
                description = ' '.join(lines[description_start_idx:-1]).strip()
                amount = None
            else:
                description = ' '.join(lines[description_start_idx:-2]).strip()
                amount = self.__get_float(lines[-2].strip())
            symbol = None
        if version == 2:
            transaction_type = lines[0].strip()
            symbol = lines[1].replace('#', '').strip()
            if len(symbol) > 5: return
            quantity = self.__get_float(lines[2].strip())
            if quantity != None: description_start_idx = 3
            else: description_start_idx = 2

            if transaction_type in [
                'ADJUSTMENT', 'IRA INTRL TRNSFR OUT', 'IRA DISTRIBUTION', 'IRA INTRL TRNSFR IN',
                'ACCOUNT TRANSFER', 'RECEIVE SECURITIES', 'NAME CHANGE', 'REVERSE SPLIT', 'CORPORATE ACTION']:
                description = ' '.join(lines[description_start_idx:-1]).strip()
                amount = None
            else:
                description = ' '.join(lines[description_start_idx:-2]).strip()
                amount = self.__get_float(lines[-1].strip())

        if version == 3:
            transaction_type = lines[0].strip()
            quantity = self.__get_float(lines[1].strip())
            description = lines[2].strip()
            amount = self.__get_float(lines[4].strip())
            symbol = None

        # get security and comments from description
        security, comments = self.__get_security_comments(description, symbol, account_number)
        
        transaction['type'] = transaction_type
        transaction['security'] = security
        transaction['symbol'] = symbol
        transaction['cusip'] = None
        transaction['comments'] = comments
        transaction['quantity'] = quantity
        transaction['amount'] = amount

        # pp(transaction)

    def __get_security_comments(self, description, symbol, account_number):
        account = self.accounts[account_number]
        
        for security, security_data in account['holdings'].items():
            if symbol != None and symbol == security_data['symbol']:
                if security in description:
                    comments = description.replace(security, '').strip()
                    return (security, comments)
                else:
                    return (security, None)
            elif security in description:
                comments = description.replace(security, '').strip()
                return (security, comments)
        
        return (description, None)
    
    def __trim_account_lines(self, lines, account_number):
        for line_idx in range(len(lines)):
            line = lines[line_idx]
            if line.startswith('Page'):
                # print('%s: %s' % (self.name, self.statement.pdf_file))
                # for line in lines:
                #     print('\t%s' % line)
                lines = lines[:line_idx]
                if account_number in lines:
                    lines = lines[:lines.index(account_number)]
                while self.__get_float(lines[-1]) == None:
                    lines = lines[:-1]
                return lines
        return lines

    def __get_symbol_cusip(self, name):
        if len(name) == 9:
            return (None, name)
        return (name, None)
    
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
            children = account_data['Account']['children']

            lines = children['SECURITY POSITIONS']['lines']
            if len(lines) > 0:
                # print('\tSECURITY POSITIONS')
                self.__add_stock(lines, account_number)

    def __add_stock(self, lines, account_number):
        # add core data to account holdings
        account = self.accounts[account_number]

        # lines = lines[lines.index('Cur. Yld')+1:]
        lines = self.__trim_lines(lines, account_number, 'Cur. Yld')

        for line_idx in range(len(lines)):
            line = lines[line_idx]
            if line in ['CASH', 'MARGIN']:
                symbol = lines[line_idx+1]
                if symbol.endswith('XX'):
                    security_type = 'money market fund'
                elif symbol.endswith('X'):
                    security_type = 'mutual fund'
                else:
                    security_type = 'stock'
                quantity = self.__get_float(lines[line_idx+2])
                security = lines[line_idx+3]
                account['holdings'][security] = {
                    'type': security_type, 'symbol': symbol, 'cusip': None, 'date': account['end_date'], 'quantity': quantity, 'transactions': []}

    def __get_float(self, text):
        text = text.replace('$', '')
        text = text.replace(',', '')
        try:
            return float(text)
        except:
            return None

    def __trim_lines(self, lines, account_number, start_string=None):
        trim_blocks = []
        trim_block = []
        for line in lines:
            if line.startswith('Page '):
                trim_blocks.append(trim_block)
                trim_block = []
                continue
            trim_block.append(line)
        trim_blocks.append(trim_block)

        new_lines = []
        # add trim blocks together
        for block in trim_blocks:
            if start_string is not None and start_string in block:
                # trim each block with start string if available
                new_lines += block[block.index(start_string)+1:]
            else:
                new_lines += block

        return new_lines

    def __set_accounts_info(self):
        for account_number, account_data in self.__name_pages['accounts'].items():
            self.accounts[account_number] = {'statement': self.statement.pdf_file, 'holdings': {}}
            page_num = account_data['Account']['pages'][0]
            blocks = self.statement.get_page_blocks(page_num)
            for block_idx in range(len(blocks)):
                block = blocks[block_idx]
                if block[0] == 'Period Beginning':
                    self.accounts[account_number]['start_date'] = datetime.strptime(blocks[block_idx+1][0].strip(), '%m / %d / %Y')
                    self.accounts[account_number]['end_date'] = datetime.strptime(blocks[block_idx+1][1].strip(), '%m / %d / %Y')
                    self.accounts[account_number]['type'] = None
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
                    'CASH ACCOUNT ACTIVITY': {
                        'stop': 'CLOSING BALANCE',
                        'lines': [],
                    },
                    'MARGIN ACCOUNT ACTIVITY': {
                        'stop': 'CLOSING BALANCE',
                        'lines': [],
                    },
                    'BANK DEPOSIT ACTIVITY': {
                        'stop': 'CLOSING BALANCE',
                        'lines': [],
                    },
                    'TRADES PENDING SETTLEMENT': {
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
                account_number = blocks[block_idx+1][0]
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
                                # for line in block:
                                #     # if 'Contin' in line or 'contin' in line or 'CONTIN' in line:
                                #     # if '(continued)' in line:
                                #     if 'TRADES PENDING SETTLEMENT' in line:
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
                # since they have no (continued) in the name
                if current_name == line: continue
                current_name = line
                current_lines = []
                continue

            if current_name != None:
                current_lines.append(line)
        
        if current_name != None:
            name_pages[current_name]['lines'] = current_lines
            # raise Exception('last current name not stopped: %s' % current_name)
            # print('%s: %s' % (self.name, self.statement.pdf_file))
            # print(current_name)
            # for line in current_lines:
            #     print('\t%s' % line)

        for name, name_data in name_pages.items():
            if 'children' in name_data:
                self.__recurse_lines(name_data['children'], name_data['lines'])
