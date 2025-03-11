from datetime import datetime
from pprint import pp
import math, copy
import pandas as pd

class Etrade():
    name = 'Etrade'

    def __init__(self, statement):
        self.statement = statement
        self.accounts = {}

        # if self.statement.pdf_file != 'database/statements_ms\\Etrade 2014-07-08.pdf': return
        # if self.statement.pdf_file != 'database/statements_ms\\RO_2022_11.pdf': return

        # return

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
            
            children = account_data['Account Number:']['children']
            
            activities = [
                'SECURITIES PURCHASED OR SOLD',
                'MUTUAL FUNDS PURCHASED OR SOLD',
                'DIVIDENDS & INTEREST ACTIVITY',
                'OTHER ACTIVITY',
            ]

            for activity in activities:
                lines = children[activity]['lines']
                if len(lines) > 0:
                    print('\t%s' % activity)
                    self.__get_transactions(lines, account_number)

    def __get_transactions(self, lines, account_number):
        account = self.accounts[account_number]
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
                        # self.__add_transaction(current_transaction)
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
            # self.__add_transaction(current_transaction)

    def __parse_transaction(self, transaction):
        lines = transaction.pop('lines')
        lines = self.__trim_transaction_lines(lines)

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
            transaction['symbol'], transaction['cusip'] = self.__get_symbol_cusip(transaction['symbol'])
            transaction['security'] = ' '.join(lines[1:-2]).lstrip('*')
            # transaction['security'], transaction['comments'] = self.__fix_security_name(transaction['security'], transaction['symbol'])
            values = lines[-1:]
        else:
            transaction['symbol'] = lines[type_idx-1]
            transaction['symbol'], transaction['cusip'] = self.__get_symbol_cusip(transaction['symbol'])
            transaction['security'] = ' '.join(lines[:type_idx-1]).lstrip('*')
            values = lines[type_idx+1:]
        transaction['security'], transaction['comments'] = self.__fix_security_name(transaction['security'],
            transaction['symbol'], transaction['cusip'])
        
        # handle values

        # quantity, price, amount: Bought, Sold
        if transaction_type in ['Bought', 'Sold']:
            transaction['quantity'] = self.__get_float(values[0])
            transaction['price'] = self.__get_float(values[1])
            # transaction['amount'] = self.__get_float(values[2])

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
            # print(transaction['type'])
        
        pp(transaction)

    def __fix_security_name(self, security, symbol, cusip):
        account = self.accounts[list(self.accounts.keys())[0]]
        for holding, holding_data in account['holdings'].items():
            if symbol != None and symbol == holding_data['symbol']:
                if security != holding:
                    splits = security.split(holding)
                    if len(splits) == 2:
                        return (holding, splits[1].strip())
                    else:
                        raise Exception('security: %s, holding: %s' % (security, holding))
                return (holding, None)

            if cusip != None and cusip == holding_data['cusip']:
                if security != holding:
                    splits = security.split(holding)
                    if len(splits) == 2:
                        return (holding, splits[1].strip())
                    else:
                        same_name = ''
                        for c1, c2 in zip(security, holding):
                            if c1 != c2: break
                            same_name += c1
                        same_name = same_name.strip()
                        if len(same_name) > 0:
                            splits = security.split(same_name)
                            if len(splits) == 2:
                                return (holding, splits[1].strip())
                            else:
                                raise Exception('security: %s, holding: %s' % (security, holding))

                return (holding, None)

        return (security, None)

    def __trim_transaction_lines(self, lines):
        index = 0
        for line in lines:
            if 'PAGE ' in line and ' OF ' in line:
                return lines[:index]
            index += 1
        return lines

    def __set_holdings(self):
        for account_number, account_data in self.__name_pages['accounts'].items():
            # print(account_number)

            children = account_data['Account Number:']['children']
        
            lines = children['CASH & CASH EQUIVALENTS  (']['lines']
            if len(lines) > 0:
                # print('\tCASH & CASH EQUIVALENTS')
                self.__add_money_market(lines, account_number, 'CASH & CASH EQUIVALENTS')
            
            lines = children['CASH & CASH EQUIVALENTS (']['lines']
            if len(lines) > 0:
                # print('\tCASH & CASH EQUIVALENTS')
                self.__add_money_market(lines, account_number, 'CASH & CASH EQUIVALENTS')

            lines = children['STOCKS, OPTIONS & EXCHANGE-TRADED FUNDS']['lines']
            if len(lines) > 0:
                # print('\tSTOCKS, OPTIONS & EXCHANGE-TRADED FUNDS')
                self.__add_stock(lines, account_number, 'stock', 'YIELD (%)', 'STOCKS, OPTIONS & EXCHANGE-TRADED FUNDS')

            lines = children['MUTUAL FUNDS  (']['lines']
            if len(lines) > 0:
                # print('\tMUTUAL FUNDS')
                self.__add_stock(lines, account_number, 'mutual fund', 'INCOME', 'MUTUAL FUNDS')

            lines = children['MUTUAL FUNDS (']['lines']
            if len(lines) > 0:
                # print('\tMUTUAL FUNDS')
                self.__add_stock(lines, account_number, 'mutual fund', 'INCOME', 'MUTUAL FUNDS')
            
            lines = children['TREASURIES']['lines']
            if len(lines) > 0:
                # print('\tTREASURIES')
                self.__add_bill(lines, account_number, 't bill', 'YIELD (%)', 'TREASURIES')

            lines = children['CD']['lines']
            if len(lines) > 0:
                # print('\tCD')
                self.__add_bill(lines, account_number, 'cd', 'YIELD (%)', 'CD')

    def __add_money_market(self, lines, account_number, page_name):
        account = self.accounts[account_number]

        # find start string and remove start and pages
        if 'AMOUNT' in lines:
            start_string = 'AMOUNT'
        elif 'BALANCE' in lines:
            start_string = 'BALANCE'
        lines = self.__trim_lines(lines, page_name, start_string)

        # HACK but it works, no new statements will be this class
        mmfs = {
            'VANGUARD MONEY MKT RESERVES': ['VANGUARD MONEY MARKET RESERVES INC-FEDERAL', 'VMFXX'],
            'VANGUARD ADMIRAL US TREAS FD': ['VANGUARD TREASURY MONEY MARKET FUND', 'VUSXX'],
            'VANGUARD TRSY MMF INVSTR SHRS': ['VANGUARD TREASURY MONEY MARKET FUND', 'VUSXX'],
            'JPM LIQUID ASSET FD E*TRADE CL': ['JPMORGAN TR II LIQUID ASSETS MONEY MKT FD ETRADE CL', 'JLEXX'],
        }
        for line_idx in range(len(lines)):
            line = lines[line_idx]
            if line in mmfs.keys():
                security = mmfs[line][0]
                symbol = mmfs[line][1]
                symbol, cusip = self.__get_symbol_cusip(symbol)
                mmf_idx = line_idx
                quantity = None
                while mmf_idx < len(lines) and quantity == None:
                    if lines[mmf_idx] == 'Closing Balance':
                        quantity = self.__get_float(lines[mmf_idx+2])
                    mmf_idx += 1
                account['holdings'][security] = {
                    'type': 'money market fund', 'symbol': symbol, 'cusip': cusip, 'quantity': quantity, 'date': account['end_date'], 'total_cost': quantity, 'transactions': []}


    def __add_stock(self, lines, account_number, stock_type, start_string, page_name):
        account = self.accounts[account_number]
        lines = self.__trim_lines(lines, page_name, start_string)

        while len(lines) > 0:
            lines[0] = lines[0].lstrip('*')
            if 'Cash' in lines and 'StkPln' in lines: next_idx = min(lines.index('Cash'), lines.index('StkPln'))
            elif 'Cash' in lines and not 'StkPln' in lines: next_idx = lines.index('Cash')
            elif not 'Cash' in lines and 'StkPln' in lines: next_idx = lines.index('StkPln')
            else:
                raise Exception('No Cash or StkPln in stock holdings')
            security = ' '.join(lines[:next_idx-1]).strip()
            symbol = lines[next_idx-1].strip()
            symbol, cusip = self.__get_symbol_cusip(symbol)
            quantity = self.__get_float(lines[next_idx+1])
            account['holdings'][security] = {
                'type': stock_type, 'symbol': symbol, 'cusip': cusip, 'quantity': quantity, 'date': account['end_date'], 'total_cost': None, 'transactions': []}
            next_idx += 2
            while not lines[next_idx].isupper():
                next_idx += 1
                if next_idx == len(lines): break
            if next_idx != len(lines):
                lines = lines[next_idx:]
            else:
                lines = []

    def __add_bill(self, lines, account_number, bill_type, start_string, page_name):
        # add bill data to holdings
        account = self.accounts[account_number]
        lines = self.__trim_lines(lines, page_name, start_string)

        if bill_type == 't bill': search_line = 'UNITED STATES'
        elif bill_type == 'cd': search_line = 'JP MORGAN CHASE BANK'
        
        # chop security lines into sublines and feed to add
        while search_line in lines:
            lines = lines[lines.index(search_line):]
            if search_line in lines[1:]:
                search_line_idx = lines[1:].index(search_line)+1
                bill_lines = lines[:search_line_idx]
                lines = lines[search_line_idx:]
            else:
                bill_lines = lines
                lines = []

            if bill_type == 't bill': self.__add_t_bill(bill_lines, account_number)
            elif bill_type == 'cd': self.__add_cd(bill_lines, account_number)

    def __add_cd(self, lines, account_number):
        # add cd data to holdings
        account = self.accounts[account_number]
        
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
            'type': 'cd', 'symbol': None, 'cusip': cusip, 'face_value': face_value, 'date': account['end_date'], 'total_cost': None, 'rate': rate,
            'issue_date': issue_date, 'mature_date': mature_date, 'transactions': []}

    def __add_t_bill(self, lines, account_number):
        # add t bill data to holdings
        account = self.accounts[account_number]
        
        cash_line_idx = lines.index('Cash')
        values = lines[cash_line_idx+1:]

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
            'type': 't bill', 'symbol': None, 'cusip': cusip, 'face_value': face_value, 'date': account['end_date'], 'total_cost': None,
            'issue_date': issue_date, 'mature_date': mature_date, 'reissue_date': reissue_date, 'transactions': []}

    def __trim_lines(self, lines, page_name, start_string=None):
        continued = page_name + (' (Continued)')
        trim_blocks = [] 
        # cut lines into page blocks
        while continued in lines:
            # print('found continued: %s: %s' % (page_name, self.statement.pdf_file))
            continues_idx = lines.index(continued)
            trim_block = []
            # add lines till 'PAGE '
            for line in lines[:continues_idx]:
                if line.startswith('PAGE '): break
                trim_block.append(line)
            trim_blocks.append(trim_block)
            lines = lines[continues_idx+1:]
        # add lines till 'PAGE '
        trim_block = []
        for line in lines:
            if line.startswith('PAGE '): break
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

    def __check_continued(self, lines, page_name, account_number):
        continued = page_name + (' (Continued)')
        if continued in lines:
            message = 'continued in: %s - account: %s - file: %s' % (page_name , account_number, self.statement.pdf_file)
            raise Exception(message)


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

    def __set_accounts_info(self):
        for account_number, account_data in self.__name_pages['accounts'].items():
            self.accounts[account_number] = {'holdings': {}}
            page_num = account_data['Account Number:']['pages'][0]
            for block in self.statement.get_page_blocks(page_num):
                if block[0].startswith('Account Number:'):
                    # get account data
                    self.accounts[account_number]['type'] = block[2].split(':')[-1].strip()

                    account_period = block[1].split(':')[-1].strip()
                    dates = account_period.split('-')
                    self.accounts[account_number]['start_date'] = datetime.strptime(dates[0].strip(), '%B %d, %Y')
                    self.accounts[account_number]['end_date'] = datetime.strptime(dates[1].strip(), '%B %d, %Y')
                    
                    break

    def __set_name_pages(self):
        # search structure:
        # key words under children are the start key words of blocks of lines
        # the 'stop' keyword is the end key word of blocks of those lines
        # the 'lines' feyword has all the lines of that block
        self.__name_pages = {
            'accounts': {},
            'Account Number:': {
                'pages': [],
                'children': {
                    # holdings: these blocks contain the security holdings of the account
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
                    
                    # activities: these blocks contain the security holdings of the account
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
                        'stop': ['TOTAL CONTRIBUTIONS & DISTRIBUTIONS', 'RETIREMENT SWEEP DEPOSIT ACCOUNT PROGRAM (RSDA) ACTIVITY'],
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
                            'RETIREMENT SWEEP DEPOSIT ACCOUNT PROGRAM (RSDA) ACTIVITY',
                        ],
                        'lines': [],
                    },
                },
            },
        }

        # search for pages that contain the 'Account Number:' to retrieve account number and their pages
        for page_num, blocks in self.statement.get_blocks().items():
            for block in blocks:
                # print('%s: %s' % (block[0], page_num))
                if block[0].startswith('Account Number:'):
                    account_number = block[0].split(':')[-1].strip()
                    if account_number not in self.__name_pages['accounts']:
                        self.__name_pages['accounts'][account_number] = {}
                        self.__name_pages['accounts'][account_number]['Account Number:'] = copy.deepcopy(self.__name_pages['Account Number:'])
                    self.__name_pages['accounts'][account_number]['Account Number:']['pages'].append(page_num)
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
                                #     if 'Continued' in line:
                                #         print(line)
                                #         print('\t%s' % self.statement.pdf_file)
                                lines += block
                        self.__recurse_lines(page_data['children'], lines)

    def __recurse_lines(self, name_pages, lines):
        current_name = None
        current_lines = []
        for line in lines:
            
            # check if current lines block should be stopped
            if current_name != None:
                if 'stop' in name_pages[current_name]:
                    # go through stop keywords and check if line starts with it
                    for stop_line in name_pages[current_name]['stop']:
                        if line.startswith(stop_line):
                            # print('stop: %s with: %s' % (current_name, stop_line))
                            name_pages[current_name]['lines'] = current_lines
                            current_name = None
                            current_lines = []
                            break
                    if current_name == None: continue
            
            found_start = False
            # check if current lines block should start
            # go through start keywords and check if line starts with it
            for key in name_pages.keys():
                if line.startswith(key) and key != current_name:
                    if current_name != None:
                        # print('%s: %s' % (self.name, self.statement.pdf_file))
                        # print('not stopped: %s before start of: %s' % (current_name, key))
                        name_pages[current_name]['lines'] = current_lines
                    # print('start: new: %s old: %s' % (key, current_name))
                    current_name = key
                    current_lines = []
                    found_start = True
                    break
            # since this line is a start key, skip it
            if found_start: continue

            # collect lines for current keyword block
            if current_name != None:
                current_lines.append(line)

        if current_name != None:
            name_pages[current_name]['lines'] = current_lines
            # print('%s: %s' % (self.name, self.statement.pdf_file))
            # print('last current name not stopped: %s' % current_name)
            # raise Exception('last current name not stopped: %s' % current_name)
            # print('%s: %s' % (self.name, self.statement.pdf_file))
            # print(current_name)
            # # for line in current_lines:
            # #     print('\t%s' % line)

        # recurse through children each keyword's children with found lines
        for name, name_data in name_pages.items():
            if 'children' in name_data:
                self.__recurse_lines(name_data['children'], name_data['lines'])
