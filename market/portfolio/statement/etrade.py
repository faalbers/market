from datetime import datetime
from pprint import pp
import math
import pandas as pd

class Etrade():
    name = 'Etrade'

    def __init__(self, statement):
        self.statement = statement
        self.accounts = {}
        if self.statement.pdf_file != 'database/statements_ms\\Etrade-7273_TRUST_2015-02.pdf': return
        # print('%s: %s' % (self.name, self.statement.pdf_file))
        # self.__test()
        # self.__set_name_pages()
        # self.__test_b()
        # return
    
        # print('')
        # print('%s: %s' % (self.name, self.statement.pdf_file))

        self.__set_name_pages()
        self.__set_accounts_info()
        self.__set_holdings()
        self.__set_transactions()

        # pp(self.accounts)

    def __test_b(self):
        holdings = self.__name_pages['Account Number']['children']

        lines = holdings['MUTUAL FUNDS  (']['lines']
        for line in lines:
            print('\t%s' % line)

    def __test(self):
        found = False
        for line in self.statement.get_lines():
            if line.startswith('MUTUAL FUNDS PURCHASED OR SOLD'):
                found = True
            if found and line.startswith('TOTAL MUTUAL FUNDS ACTIVITY'):
                found = False
            # if found and line.startswith('TOTAL PRICED PORTFOLIO HOLDINGS ('):
            #     found = False
            # if found and line.startswith('OTHER ACTIVITY'):
            #     found = False
        if found: print(self.statement.pdf_file)

    def __set_transactions(self):
        name_page_children = self.__name_pages['Account Number']['children']

        activities = [
            'SECURITIES PURCHASED OR SOLD',
            'MUTUAL FUNDS PURCHASED OR SOLD',
            'DIVIDENDS & INTEREST ACTIVITY',
            'OTHER ACTIVITY',
        ]

        for activity in activities:
            lines = name_page_children[activity]['lines']
            if len(lines) > 0:
                # print('\t%s' % activity)
                self.__add_transactions(lines)
        
    def __add_transactions(self, lines):
        last_index = None
        current_transaction = {}
        found_float = True
        for line_index in range(len(lines)):
            line = lines[line_index]
            line_digits = line.replace('/', '')
            if found_float and line_digits.isdigit() and line != line_digits and len(line_digits) == 6:
                # create a datetime object from the date line
                date = datetime.strptime(line, '%m/%d/%y')

                if last_index != None:
                    # check index difference between date line and last date line
                    diff_index = line_index - last_index
                    if diff_index <= 2:
                        # looks like we have a Settlement Date
                        current_transaction['settlement_date'] = date
                    else:
                        # we got to the next Transaction Date
                        # store the last one and create a new one
                        self.__parse_transaction(current_transaction)
                        self.__add_transaction(current_transaction)
                        current_transaction = {'transaction_date': date, 'lines': []}
                else:
                    # this is the first Transaction Date, create a new one
                    current_transaction = {'transaction_date': date, 'lines': []}
                
                # set index since last date line
                last_index = line_index
            elif 'transaction_date' in current_transaction:
                # ignore '12:34' time line
                if not(len(line) == 5 and line.replace(':', '').isdigit()):
                    if len(current_transaction['lines']) == 0: found_float = False
                    current_transaction['lines'].append(line)
                    if self.__get_float(line) != None:
                        found_float = True
        
        # make sure the last transaction is added if needed
        if 'transaction_date' in current_transaction:
            self.__parse_transaction(current_transaction)
            self.__add_transaction(current_transaction)

    def __add_transaction(self, transaction):
        if not 'type' in transaction: return
        account = self.accounts[list(self.accounts.keys())[0]]
        security = transaction.pop('security')
        symbol = transaction.pop('symbol')
        if security in account['holdings']:
            # print(security)
            # for security in account['holdings']:
            #     print('\t%s' % security)
            if symbol != None and account['holdings'][security]['symbol'] != symbol:
                account['holdings'][security]['symbol'] = symbol
            account['holdings'][security]['transactions'].append(transaction)
        else:
            # print('%s: %s' % (self.name, self.statement.pdf_file))
            # print(security)
            # for security in account['holdings']:
            #     print('\t%s' % security)
            pass
            # account['holdings'][security] = {'type': None, 'symbol': None, 'date': account['end_date'], 'transactions': []}
            # account['holdings'][security]['transactions'].append(transaction)

    def __parse_transaction(self, transaction):
        self.__trim_transaction_lines(transaction)
        lines = transaction.pop('lines')

        transaction_types = [ 
            'Bought', 'Sold', # 'SECURITIES PURCHASED OR SOLD', 'MUTUAL FUNDS PURCHASED OR SOLD'
            'Dividend', 'Capital Gain', # 'DIVIDENDS & INTEREST ACTIVITY'
            'Dividend', 'Reinvest', 'Redemption', 'Conversion', 'Merger', 'Fee', 'Adjustment', 'Journal', 'Receive', 'Cash-in-Lieu', # 'OTHER ACTIVITY'
        ]
        
        # get transaction type
        transaction_type = None
        for transaction_search_type in transaction_types:
            if transaction_search_type in lines:
                transaction_type = transaction_search_type
                break
        if transaction_type == None: return

        transaction['type'] = transaction_type
        type_idx = lines.index(transaction['type'])

        # get security , symbol and values
        if type_idx == 0:
            transaction['symbol'] = lines[-2]
            transaction['security'] = ' '.join(lines[1:-2]).lstrip('*')
            transaction['security'], transaction['comments'] = self.__fix_security_name(transaction['security'], transaction['symbol'])
            values = lines[-1:]
        else:
            transaction['symbol'] = lines[type_idx-1]
            transaction['security'] = ' '.join(lines[:type_idx-1]).lstrip('*')
            transaction['security'], transaction['comments'] = self.__fix_security_name(transaction['security'], transaction['symbol'])
            values = lines[type_idx+1:]
            
        # handle values

        # quantity, price, amount: Bought, Sold
        if transaction_type in ['Bought', 'Sold']:
            transaction['quantity'] = self.__get_float(values[0])
            transaction['price'] = self.__get_float(values[1])
            transaction['amount'] = self.__get_float(values[2])

        # amount: Dividend, Capital Gain, Fee, Cash-in-Lieu
        elif transaction_type in ['Dividend', 'Capital Gain', 'Fee', 'Cash-in-Lieu']:
            transaction['amount'] = self.__get_float(values[0])

        # quantity, amount: Reinvest, Redemption
        elif transaction_type in ['Reinvest', 'Redemption']:
            transaction['quantity'] = self.__get_float(values[0])
            transaction['amount'] = self.__get_float(values[1])

        # quantity: Adjustment, Conversion, Journal, Receive
        elif transaction_type in ['Adjustment', 'Conversion', 'Journal', 'Receive']:
            transaction['quantity'] = self.__get_float(values[0])

        # quantity or [quantity, amount]: Merger
        elif transaction_type in ['Merger']:
            transaction['quantity'] = self.__get_float(values[0])
            if len(values) > 1:
                transaction['amount'] = self.__get_float(values[1])

        else:
            pass
            print(transaction['type'])
        
        # pp(transaction)

    def __fix_security_name(self, security, symbol):
        account = self.accounts[list(self.accounts.keys())[0]]
        for holding in account['holdings']:
            trim_start = holding
            holding_symbol = account['holdings'][holding]['symbol']
            if holding_symbol != None and holding_symbol == symbol:
                if holding.endswith(symbol):
                    trim_start = ' '.join(holding.split(' ')[:-1])
                comments = security.replace(trim_start, '').strip()
                if comments == '': comments = None
                return (holding, comments)
            elif security.startswith(trim_start):
                comments = security.replace(trim_start, '').strip()
                if comments == '': comments = None
                return (holding, comments)
        return (security, None)

    def __trim_transaction_lines(self, transaction):
        index = 0
        for line in transaction['lines']:
            if 'PAGE ' in line and ' OF ' in line:
                transaction['lines'] = transaction['lines'][:index]
                return
            index += 1

    def __set_holdings(self):
        holdings = self.__name_pages['Account Number']['children']

        lines = holdings['CASH & CASH EQUIVALENTS  (']['lines']
        if len(lines) > 0:
            # print('\tCASH & CASH EQUIVALENTS')
            self.__add_money_market(lines)
        
        lines = holdings['CASH & CASH EQUIVALENTS (']['lines']
        if len(lines) > 0:
            # print('\tCASH & CASH EQUIVALENTS')
            self.__add_money_market(lines)

        lines = holdings['STOCKS, OPTIONS & EXCHANGE-TRADED FUNDS']['lines']
        if len(lines) > 0:
            # print('\tSTOCKS, OPTIONS & EXCHANGE-TRADED FUNDS')
            self.__add_stock(lines, 'stock', 'YIELD (%)')

        lines = holdings['MUTUAL FUNDS  (']['lines']
        if len(lines) > 0:
            # print('\tMUTUAL FUNDS')
            self.__add_stock(lines, 'mutual fund', 'INCOME')

        lines = holdings['MUTUAL FUNDS (']['lines']
        if len(lines) > 0:
            # print('\tMUTUAL FUNDS')
            self.__add_stock(lines, 'mutual fund', 'INCOME')
        
        lines = holdings['TREASURIES']['lines']
        if len(lines) > 0:
            # print('\tTREASURIES')
            self.__add_bill(lines, 't bill')

        lines = holdings['CD']['lines']
        if len(lines) > 0:
            # print('\tCD')
            self.__add_bill(lines, 'cd')

    def __add_money_market(self, lines):
        # for line in lines:
        #     print('\t%s' % line)
        # add cash data to account holdings
        account_number = list(self.accounts.keys())[0]
        account = self.accounts[account_number]
        
        account_line = 'Account Number:  '+account_number
        new_lines = []
        if 'AMOUNT' in lines:
            start_string = 'AMOUNT'
        elif 'BALANCE' in lines:
            start_string = 'BALANCE'
        else:
            raise Exception('No AMOUNT or BALANCE start string in money market holdings')
        while start_string in lines:
            lines = lines[lines.index(start_string)+1:]
            if account_line in lines:
                new_lines += lines[:lines.index(account_line)-1]
                lines = lines[lines.index(account_line):]
            else:
                new_lines += lines
        mmfs = {
            'VANGUARD MONEY MKT RESERVES': ['VANGUARD MONEY MARKET RESERVES INC-FEDERAL', 'VMFXX'],
            'VANGUARD ADMIRAL US TREAS FD': ['VANGUARD TREASURY MONEY MARKET FUND', 'VUSXX'],
            'VANGUARD TRSY MMF INVSTR SHRS': ['VANGUARD TREASURY MONEY MARKET FUND', 'VUSXX'],
            'JPM LIQUID ASSET FD E*TRADE CL': ['JPMORGAN TR II LIQUID ASSETS MONEY MKT FD ETRADE CL', 'JLEXX'],
        }
        for line_idx in range(len(new_lines)):
            line = new_lines[line_idx]
            if line in mmfs.keys():
                security = mmfs[line][0]
                symbol = mmfs[line][1]
                mmf_idx = line_idx
                quantity = None
                while mmf_idx < len(new_lines) and quantity == None:
                    if new_lines[mmf_idx] == 'Closing Balance':
                        quantity = self.__get_float(new_lines[mmf_idx+2])
                    mmf_idx += 1
                account['holdings'][security] = {
                    'type': 'money market fund', 'symbol': symbol, 'quantity': quantity, 'total_cost': quantity, 'transactions': []}
                
    def __add_stock(self, lines, stock_type, start_string):
        # add stock data to account holdings
        account_number = list(self.accounts.keys())[0]
        account = self.accounts[account_number]
        
        account_line = 'Account Number:  '+account_number
        new_lines = []
        while start_string in lines:
            lines = lines[lines.index(start_string)+1:]
            if account_line in lines:
                new_lines += lines[:lines.index(account_line)-1]
                lines = lines[lines.index(account_line):]
            else:
                new_lines += lines

        while len(new_lines) > 0:
            new_lines[0] = new_lines[0].lstrip('*')
            if 'Cash' in new_lines and 'StkPln' in new_lines: next_idx = min(new_lines.index('Cash'), new_lines.index('StkPln'))
            elif 'Cash' in new_lines and not 'StkPln' in new_lines: next_idx = new_lines.index('Cash')
            elif not 'Cash' in new_lines and 'StkPln' in new_lines: next_idx = new_lines.index('StkPln')
            else:
                raise Exception('No Cash or StkPln in stock holdings')
            security = ' '.join(new_lines[:next_idx-1]).strip()
            symbol = new_lines[next_idx-1].strip()
            quantity = self.__get_float(new_lines[next_idx+1])
            account['holdings'][security] = {
                'type': stock_type, 'symbol': symbol, 'quantity': quantity, 'total_cost': None, 'transactions': []}
            next_idx += 2
            while not new_lines[next_idx].isupper():
                next_idx += 1
                if next_idx == len(new_lines): break
            if next_idx != len(new_lines):
                new_lines = new_lines[next_idx:]
            else:
                new_lines = []
    
    def __add_bill(self, lines, bill_type):
        # add bill data to holdings
        account_number = list(self.accounts.keys())[0]
        account = self.accounts[account_number]
        
        account_line = 'Account Number:  '+account_number
        new_lines = []
        while 'YIELD (%)' in lines:
            lines = lines[lines.index('YIELD (%)')+1:]
            if account_line in lines:
                new_lines += lines[:lines.index(account_line)-1]
                lines = lines[lines.index(account_line):]
            else:
                new_lines += lines
        
        if bill_type == 't bill': search_line = 'UNITED STATES'
        elif bill_type == 'cd': search_line = 'JP MORGAN CHASE BANK'
        
        while len(new_lines) > 0:
            new_lines = new_lines[1:]
            if search_line in new_lines:
                search_line_idx = new_lines.index(search_line)
                lines = new_lines[:search_line_idx]
                new_lines = new_lines[search_line_idx:]
            else:
                lines = new_lines
                new_lines = []
            
            if bill_type == 't bill': self.__add_t_bill(lines)
            elif bill_type == 'cd': self.__add_cd(lines)

    def __add_cd(self, lines):
        # add t bill data to holdings
        account = self.accounts[list(self.accounts.keys())[0]]
        
        cash_line_idx = lines.index('Cash')
        values = lines[cash_line_idx+1:]

        search_lines = lines[1:cash_line_idx]
        for line_idx in range(len(search_lines)):
            line = search_lines[line_idx]
            if line.startswith('DATED DATE '):
                issue_date = line.replace('DATED DATE ', '').strip()
                issue_date = datetime.strptime(issue_date, '%m/%d/%y')
            elif line.startswith('DUE '):
                splits = line.replace('DUE ', '').split(' ')
                mature_date = splits[0].strip()
                mature_date = datetime.strptime(mature_date, '%m/%d/%Y')
                rate = self.__get_float(splits[-1].strip().rstrip('%'))
            elif line.startswith('CUSIP:'):
                cusip = line.replace('CUSIP:', '').strip()
        security = 'JP MORGAN CHASE BANK NA C/D FDIC ' + cusip
        face_value = self.__get_float(values[0])
        account['holdings'][security] = {
            'type': 'cd', 'symbol': cusip, 'face_value': face_value, 'total_cost': None, 'rate': rate,
            'issue_date': issue_date, 'mature_date': mature_date, 'transactions': []}

    def __add_t_bill(self, lines):
        # add t bill data to holdings
        account = self.accounts[list(self.accounts.keys())[0]]
        
        cash_line_idx = lines.index('Cash')
        values = lines[cash_line_idx+1:]
        # if len(values) < 5: return

        reissue_date = None
        for line in lines[1:cash_line_idx]:
            if line.startswith('RE-ISSUE '):
                reissue_date = line.replace('RE-ISSUE ', '').strip()
                reissue_date = datetime.strptime(reissue_date, '%m/%d/%Y')
            elif line.startswith('DATED DATE '):
                issue_date = line.replace('DATED DATE ', '').strip()
                issue_date = datetime.strptime(issue_date, '%m/%d/%y')
            elif line.startswith('DUE '):
                mature_date = line.replace('DUE ', '').split(' ')[0].strip()
                mature_date = datetime.strptime(mature_date, '%m/%d/%Y')
            elif line.startswith('CUSIP:'):
                cusip = line.replace('CUSIP:', '').strip()
        security = 'UNITED STATES TREASURY BILL ' + cusip
        face_value = None
        if len(values) >= 5:
            face_value = self.__get_float(values[0])
        account['holdings'][security] = {
            'type': 't bill', 'symbol': cusip, 'face_value': face_value, 'total_cost': None,
            'issue_date': issue_date, 'mature_date': mature_date, 'reissue_date': reissue_date, 'transactions': []}

    def __get_float(self, text):
        if text.startswith('$'): text = text[1:]
        if text.startswith('('): text = '-'+text[1:-1]
        text = text.replace(',', '')
        try:
            return float(text)
        except:
            return None

    def __set_accounts_info(self):
        account_number = None
        account_type = None
        start_date = None
        end_date = None
        
        page_num = self.__name_pages['Account Number']['pages'][0]
        for block in self.statement.get_page_blocks(page_num):
            if block[0].startswith('Account Number:'):
                account_number = block[0].split(':')[-1].strip()
                account_type = block[2].split(':')[-1].strip()
                date = block[1].split(':')[-1].strip()
                date = date.split('-')
                start_date = datetime.strptime(date[0].strip(), '%B %d, %Y')
                end_date = datetime.strptime(date[1].strip(), '%B %d, %Y')
        self.accounts[account_number] = {
            'type': account_type,
            'start_date': start_date,
            'end_date': end_date,
            'holdings': {},
        }

    def __set_name_pages(self):
        self.__name_pages = {
            'Account Number': {
                'pages': [],
                'children': {
                    # holdings
                    'CASH & CASH EQUIVALENTS  (': {
                        'stop': ['TOTAL CASH & CASH EQUIVALENTS'],
                        'lines': [],
                    },
                    'CASH & CASH EQUIVALENTS (': {
                        'stop': ['TOTAL CASH & CASH EQUIVALENTS'],
                        'lines': [],
                    },
                    'MUTUAL FUNDS  (': {
                        'stop': ['TOTAL MUTUAL FUNDS', 'FIXED INCOME  (', 'OTHER ACTIVITY'],
                        'lines': [],
                    },
                    'MUTUAL FUNDS (': {
                        'stop': ['TOTAL MUTUAL FUNDS', 'TOTAL PRICED PORTFOLIO HOLDINGS ('],
                        'lines': [],
                    },
                    'STOCKS, OPTIONS & EXCHANGE-TRADED FUNDS': {
                        'stop': ['TOTAL STOCKS, OPTIONS & ETF', 'MUTUAL FUNDS ('],
                        'lines': [],
                    },
                    'TREASURIES': {
                        'stop': ['TOTAL TREASURIES', 'TOTAL PRICED PORTFOLIO HOLDINGS (', 'OTHER ACTIVITY'],
                        'lines': [],
                    },
                    'CD': {
                        'stop': ['TOTAL CD'],
                        'lines': [],
                    },

                    # activities
                    'SECURITIES PURCHASED OR SOLD': {
                        'stop': ['TOTAL SECURITIES ACTIVITY'],
                        'lines': [],
                    },
                    'MUTUAL FUNDS PURCHASED OR SOLD': {
                        'stop': ['TOTAL MUTUAL FUNDS ACTIVITY'],
                        'lines': [],
                    },
                    
                    # # 'MONEY FUND ACTIVITY ('
                    'DIVIDENDS & INTEREST ACTIVITY': {
                        'stop': ['TOTAL DIVIDENDS & INTEREST ACTIVITY'],
                        'lines': [],
                    },
                    'CONTRIBUTIONS & DISTRIBUTIONS ACTIVITY': {
                        'stop': ['TOTAL CONTRIBUTIONS & DISTRIBUTIONS'],
                        'lines': [],
                    },
                    'WITHDRAWALS & DEPOSITS': {
                        'stop': ['NET WITHDRAWALS & DEPOSITS'],
                        'lines': [],
                    },
                    'OTHER ACTIVITY': {
                        'stop': [
                            'TOTAL OTHER ACTIVITY',
                            'EXTENDED INSURANCE SWEEP DEPOSIT ACCOUNT (ESDA) ACTIVITY',
                            'RETIREMENT SWEEP DEPOSIT ACCOUNT PROGRAM (RSDA) ACTIVITY'
                            ],
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
                    self.__recurse_lines(page_data['children'], lines)

    def __recurse_lines(self, name_pages, lines):
        current_name = None
        for line in lines:
            
            if current_name != None:
                if 'stop' in name_pages[current_name]:
                    # if line == name_pages[current_name]['stop']:
                    #     current_name = None
                    #     continue
                    for stop_line in name_pages[current_name]['stop']:
                        if line.startswith(stop_line):
                            current_name = None
                            break
                    if current_name == None: continue
            
            # if line in name_pages.keys():
            #     current_name = line
            #     continue
            key_found = False
            for key in name_pages.keys():
                if line.startswith(key):
                    # print(line)
                    current_name = key
                    key_found = True
                    break
            if key_found: continue

            if current_name != None:
                name_pages[current_name]['lines'].append(line)

        for name, name_data in name_pages.items():
            if 'children' in name_data:
                self.__recurse_lines(name_data['children'], name_data['lines'])
