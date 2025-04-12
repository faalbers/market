from datetime import datetime
from pprint import pp
import math, copy
import pandas as pd

class Fidelity():
    name = 'Fidelity'

    def __init__(self, statement):
        self.statement = statement
        self.accounts = {}

        # if self.statement.pdf_file != 'database/statements_fi\\FrankRothIRA_2020_06.pdf': return

        # return

        # print('')
        # print('%s: %s' % (self.name, self.statement.pdf_file))

        self.__set_name_pages()
        self.__set_accounts_info()
        self.__set_holdings()
        self.__set_transactions()

        # pp(self.__name_pages['accounts'])
        # if self.statement.pdf_file == 'database/statements_fi\\FrankRothIRA_2020_03.pdf':
        #     pp(self.accounts)

    def __set_transactions(self):
        for account_number, account_data in self.__name_pages['accounts'].items():
            # print(account_number)
            
            children = account_data['Account #']['children']

            activities = [
                'Securities Bought & Sold',
                'Core Fund Activity',
                'Dividends, Interest & Other Income',
                'Securities Transferred In',
                # 'Exchanges Out',
                # 'Exchanges In',
                'Other Activity Out',
                'Transfers Between Fidelity Accounts',
            ]

            for activity in activities:
                lines = children[activity]['lines']
                if len(lines) > 0:
                    # if activity == 'Securities Bought & Sold':
                    #     print('%s: %s' % (self.name, self.statement.pdf_file))
                    # print('\t%s' % activity)
                    self.__get_transactions(lines, account_number, activity)

    def __get_transactions(self, lines, account_number, activity):
        account = self.accounts[account_number]
        current_transaction = {}
        pre_line = None
        for line_index in range(len(lines)):
            line = lines[line_index]
            line_digits = line.replace('/', '')
            if line_digits.isdigit() and line != line_digits and len(line_digits) <= 4:
                # create a datetime object from the date line
                # HACK pre_line is a hack to see if cost is a value
                if pre_line == None: pre_line = lines[line_index-4]
                date_elements = line.split('/')
                date = datetime(month=int(date_elements[0]), day=int(date_elements[1]), year=account['end_date'].year)

                if 'transaction_date' in current_transaction:
                    self.__parse_transaction(current_transaction, activity, pre_line)
                    self.__add_transaction(current_transaction, account_number)
                
                current_transaction = {'transaction_date': date, 'lines': []}

            elif 'transaction_date' in current_transaction:
                current_transaction['lines'].append(line)
        
        # make sure the last transaction is added if needed
        if 'transaction_date' in current_transaction:
            self.__parse_transaction(current_transaction, activity, pre_line)
            self.__add_transaction(current_transaction, account_number)

    def __add_transaction(self, transaction, account_number):
        account = self.accounts[account_number]
        security = transaction.pop('security')
        symbol = transaction.pop('symbol')
        cusip = transaction.pop('cusip')

        if security in account['holdings']:
            if cusip != account['holdings'][security]['cusip']:
                account['holdings'][security]['cusip'] = cusip
            account['holdings'][security]['transactions'].append(transaction)
        else:
            account['holdings'][security] = {'type': None, 'symbol': symbol, 'cusip': cusip, 'date': account['end_date'], 'transactions': []}
            account['holdings'][security]['transactions'].append(transaction)
    
    def __parse_transaction(self, transaction, activity, pre_line):   
        lines = transaction.pop('lines')
        
        transaction_types = [
            'You Bought', 'You Sold', # 'Securities Bought & Sold'
            'You Bought', 'You Sold', 'Reinvestment', 'Transferred', # 'Core Fund Activity'
            'Dividend Received', 'Interest Earned', 'Reinvestment', 'Long-Term Cap Gain', 'Short-Term Cap Gain', # 'Dividends, Interest & Other Income'
            'Transfer Of Assets', # 'Securities Transferred In'
            # 'Transferred From', 'Transferred To', # 'Exchanges In' 'Exchanges Out'
            'Transferred From', 'Transferred To', # 'Transfers Between Fidelity Accounts'
            'Redeemed', # 'Other Activity Out'
        ]
        transaction_types = set(transaction_types)

        if activity == 'Other Activity Out':
            for line_idx in range(len(lines)):
                line = lines[line_idx]
                if line in transaction_types:
                    transaction['type'] = line
                    transaction['security'] = ' '.join(lines[:line_idx-1]).strip()
                    symbol, cusip = self.__get_symbol_cusip(lines[line_idx-1])
                    if transaction['security'].startswith('UNITED STATES TREAS BILLS ZERO CPN'):
                        transaction['security'] = 'UNITED STATES TREAS BILLS ZERO CPN %s' % cusip
                    transaction['symbol'] = symbol
                    transaction['cusip'] = cusip
                    transaction['quantity'] = self.__get_float(lines[line_idx+1])
                    transaction['amount'] = self.__get_float(lines[-1])
                    return

        if activity == 'Securities Bought & Sold':
            # print(self.statement.pdf_file)
            # print('\n\t\tlines:')
            # for line in lines:
            #     print('\t\t\t%s' % line)
            for line_idx in range(len(lines)):
                line = lines[line_idx]
                if line in transaction_types:
                    transaction['type'] = line
                    transaction['security'] = ' '.join(lines[:line_idx-1]).strip()
                    # HACK
                    for split_name in ['CONF:', '0.00000% ', 'UNSOLICITED ', 'CONTRIBUTION ', '+']:
                        if split_name in transaction['security']:
                            splits = transaction['security'].split(split_name)
                            transaction['security'] = splits[0].strip()
                            transaction['comments'] = split_name + splits[1].strip()
                    symbol, cusip = self.__get_symbol_cusip(lines[line_idx-1])
                    transaction['symbol'] = symbol
                    transaction['cusip'] = cusip

                    # find values
                    if lines[line_idx+1].startswith('Transaction Profit:'):
                        if lines[line_idx+2].startswith('Transaction Loss:'):
                            values = lines[line_idx+3:]
                        else:
                            values = lines[line_idx+2:]
                    else:
                        values = lines[line_idx+1:]
                    for value_idx in range(len(values)):
                        value = values[value_idx]
                        if value.startswith('Total Securities'):
                            values = values[:value_idx]
                            break
                    
                    transaction['quantity'] = self.__get_float(values[0])
                    transaction['price'] = self.__get_float(values[1])

                    # find transaction cost
                    if pre_line == 'Cost':
                        if len(values) == 5:
                            if values[3] != '-':
                                transaction['transaction_cost'] = self.__get_float(values[3])
                        elif len(values) == 4:
                            transaction['transaction_cost'] = self.__get_float(values[2])
                    elif pre_line == 'Price':
                        if values[2] != '-':
                            transaction['transaction_cost'] = self.__get_float(values[2])
                    
                    if transaction['security'] == 'UNITED STATES TREAS BILLS ZERO CPN':
                        transaction['security'] += ' %s' % cusip
                        transaction['price'] = transaction['price'] / 100.0
                    return
                
        if activity == 'Core Fund Activity':
            for line_idx in range(len(lines)):
                line = lines[line_idx]
                if line in transaction_types:
                    transaction['type'] = line
                    transaction['security'] = lines[line_idx+1]
                    transaction['symbol'] = None
                    transaction['cusip'] = None
                    transaction['comments'] = lines[line_idx+2]
                    transaction['quantity'] = self.__get_float(lines[line_idx+3])
                    transaction['price'] = self.__get_float(lines[line_idx+4])
                    return

        if activity == 'Dividends, Interest & Other Income':
            for line_idx in range(len(lines)):
                line = lines[line_idx]
                if line in transaction_types:
                    transaction['type'] = line
                    transaction['security'] = ' '.join(lines[:line_idx-1]).strip()
                    symbol, cusip = self.__get_symbol_cusip(lines[line_idx-1])
                    transaction['symbol'] = symbol
                    transaction['cusip'] = cusip
                    if transaction['type'] == 'Reinvestment':
                        if 'AS OF' in transaction['security']:
                            transaction['security'] = transaction['security'].split('AS OF')[0].strip()
                        transaction['quantity'] = self.__get_float(lines[line_idx+1])
                        transaction['price'] = self.__get_float(lines[line_idx+2])
                    else:
                        transaction['amount'] = self.__get_float(lines[line_idx+3])
                    return

        if activity == 'Securities Transferred In':
            for line_idx in range(len(lines)):
                line = lines[line_idx]
                if line in transaction_types:
                    transaction['type'] = line
                    transaction['security'] = ' '.join(lines[:line_idx-1]).strip()
                    if 'ACAT' in transaction['security']:
                        splits = transaction['security'].split('ACAT')
                        transaction['security'] = splits[0].strip()
                        transaction['comments'] = 'ACAT ' + splits[1].strip()
                    symbol, cusip = self.__get_symbol_cusip(lines[line_idx-1])
                    transaction['symbol'] = symbol
                    transaction['cusip'] = cusip
                    transaction['quantity'] = self.__get_float(lines[line_idx+1])
                    transaction['price'] = self.__get_float(lines[line_idx+2])
                    return

        # if activity in ['Exchanges Out', 'Exchanges In']:
        #     for line_idx in range(len(lines)):
        #         line = lines[line_idx]
        #         if line in transaction_types:
        #             transaction['type'] = line
        #             transaction['security'] = ' '.join(lines[:line_idx]).strip()
        #             transaction['symbol'] = None
        #             transaction['cusip'] = None
        #             transaction['amount'] = self.__get_float(lines[line_idx+3])
        #             print(transaction['security'])
        #             return

        if activity == 'Transfers Between Fidelity Accounts':
            for line_idx in range(len(lines)):
                line = lines[line_idx]
                if line in transaction_types:
                    transaction['type'] = line
                    transaction['security'] = lines[0].strip()
                    transaction['comments'] = ' '.join(lines[1:line_idx-1]).strip()
                    symbol, cusip = self.__get_symbol_cusip(lines[line_idx-1])
                    transaction['symbol'] = symbol
                    transaction['cusip'] = cusip
                    transaction['quantity'] = self.__get_float(lines[line_idx+1])
                    transaction['price'] = self.__get_float(lines[line_idx+2])
                    if transaction['security'] == 'UNITED STATES TREAS BILLS ZERO CPN':
                        transaction['security'] += ' %s' % cusip
                        transaction['price'] = transaction['price'] / 100.0
                    return

    def __set_holdings(self):
        for account_number, account_data in self.__name_pages['accounts'].items():
            # print('%s' % account_number)
            children = account_data['Account #']['children']

            lines = children['NH PORTFOLIO 2024 (FIDELITY FUNDS)']['lines']
            if len(lines) > 0:
                # print('\tNH PORTFOLIO 2024 (FIDELITY FUNDS)')
                self.__add_holdings_nh(lines, account_number, 'NH PORTFOLIO 2024 (FIDELITY FUNDS)')
            
            lines = children['Core Account']['lines']
            if len(lines) > 0:
                # print('\tCore Account')
                self.__add_core(lines, account_number, 'Core Account')

            lines = children['Stock Funds']['lines']
            if len(lines) > 0:
                # print('\tStock Funds')
                self.__add_fund(lines, account_number, 'mutual fund', 'Stock Funds')

            lines = children['Equity ETPs']['lines']
            if len(lines) > 0:
                # print('\tEquity ETPs')
                self.__add_fund(lines, account_number, 'etf', 'Equity ETPs')

            lines = children['US Treasury/Agency Securities']['lines']
            if len(lines) > 0:
                # print('\tUS Treasury/Agency Securities')
                self.__add_bill(lines, account_number, 'US Treasury/Agency Securities')

    def __add_holdings_nh(self, lines, account_number, page_name):
        if lines[0] != '100%': return
        account = self.accounts[account_number]

        if lines[2].startswith('$'):
            quantity = self.__get_float(lines[1])
            price = self.__get_float(lines[2])
        else:
            quantity = self.__get_float(lines[2])
            price = self.__get_float(lines[3])
        
        account['holdings']['NH PORTFOLIO 2024 (FIDELITY FUNDS)'] = {
            'type': 'college fund', 'symbol': None, 'cusip': None, 'quantity': quantity, 'price': price, 'date': account['end_date'],
            'transactions': []}
        
    def __add_core(self, lines, account_number, page_name):
        # add core data to account holdings
        account = self.accounts[account_number]
        if 'EY (%)' in lines:
            start_string = 'EY (%)'
        elif '(EY)' in lines:
            start_string = '(EY)'
        
        # find index offsets
        params_list = lines[:lines.index(start_string)]
        if len(params_list) == 9:
            values_idx = -5
            description_idx = -5
        elif len(params_list) == 13:
            values_idx = -5
            description_idx = -6
        elif len(params_list) == 17:
            values_idx = -7
            description_idx = -8
        else:
            raise Exception('Unknown Core Account params: %s' % self.statement.pdf_file)
        
        lines = self.__trim_lines(lines, page_name, start_string)

        for line_idx in range(len(lines)):
            line = lines[line_idx]
            if line.isupper() and '(' in line and ')' in line:
                description = ' '.join(lines[:description_idx])
                symbol = description[description.index('('):description.index(')')+1]
                splits = description.split(symbol)
                security = splits[0].strip()
                if 'q' in security: security = security.split('q')[0].strip()
                comments = splits[1].strip()
                symbol = symbol[1:-1]
                symbol, cusip = self.__get_symbol_cusip(symbol)
                quantity = self.__get_float(lines[values_idx])
                # total_cost is hard coded because this is always money market
                account['holdings'][security] = {
                    'type': 'money market fund', 'symbol': symbol, 'cusip': cusip, 'date': account['end_date'], 'transactions': [],
                    'quantity': quantity, 'total_cost': quantity}


                continue
                print(self.statement.pdf_file)
                print(lines[:description_idx])
                print(lines[values_idx:])
                upper_search_idx = line_idx-1
                # HACK q replace
                while upper_search_idx >= 0:
                    check_line = lines[upper_search_idx].replace('q', '')
                    if check_line == '' or check_line.isupper():
                        upper_search_idx -= 1
                security = ' '.join(lines[upper_search_idx+1:line_idx+1]).replace('q NOT COVERED BY SIPC', '').strip()
                comments = lines[line_idx+1]
                splits = security.split('(')
                security = splits[0].strip()
                symbol = splits[1].replace(')', '').strip()
                symbol, cusip = self.__get_symbol_cusip(symbol)
                values = lines[line_idx+2:]
                account['holdings'][security] = {
                    'type': 'money market fund', 'symbol': symbol, 'cusip': cusip, 'date': account['end_date'], 'transactions': [],
                    'quantity': self.__get_float(values[1]), 'total_cost': self.__get_float(values[1])}

    def __add_fund(self, lines, account_number, security_type, page_name):
        # add fund data to account holdings
        account = self.accounts[account_number]
        lines = self.__trim_lines(lines, page_name)

        # HACK I did not bother to check
        if security_type == 'etf' and lines[0] == 't': lines = lines[1:]
        
        # HACK another specific one
        security_rename = {
            'RYDEX S&P MIDCAP 400 PURE GROWTH CLASS H': 'RYDEX MID CAP GROWTH H CLASS',
        }
        for line_idx in range(len(lines)):
            line = lines[line_idx]
            if line.isupper() and '(' in line and ')' in line:
                upper_search_idx = line_idx-1
                while upper_search_idx >= 0 and lines[upper_search_idx].isupper(): upper_search_idx -= 1
                security = ' '.join(lines[upper_search_idx+1:line_idx+1]).strip()
                splits = security.split('(')
                security = splits[0].strip()
                # HACK: remove 'EAI' and 'EY' on continues
                if len(security) < 4: continue
                symbol = splits[1].replace(')', '').strip()
                symbol, cusip = self.__get_symbol_cusip(symbol)
                values = lines[line_idx+1:]
                # HACK another specific one
                if security in security_rename: security = security_rename[security]
                account['holdings'][security] = {
                    'type': security_type, 'symbol': symbol, 'cusip': cusip, 'date': account['end_date'], 'transactions': [],
                    'quantity': self.__get_float(values[1]), 'total_cost': self.__get_float(values[4])}

    def __add_bill(self, lines, account_number, page_name):
        # add bill data to account holdings
        account = self.accounts[account_number]
        lines = self.__trim_lines(lines, page_name)

        for line_idx in range(len(lines)):
            line = lines[line_idx]
            if line.count('/') == 2:
                upper_search_idx = line_idx-1
                while upper_search_idx >= 0 and lines[upper_search_idx].isupper() and not lines[upper_search_idx].startswith('ZERO COUPON CUSIP'):
                    upper_search_idx -= 1
                security = ' '.join(lines[upper_search_idx+1:line_idx]).strip()
                mature_date = datetime.strptime(lines[line_idx], '%m/%d/%y')
                values = lines[line_idx+1:]
                face_value = self.__get_float(values[1])
                total_cost = self.__get_float(values[5])
                for value in values:
                    if value.startswith('ZERO COUPON CUSIP:'):
                        cusip = value.replace('ZERO COUPON CUSIP:', '').strip()
                        security += ' %s' % cusip
                        break
                account['holdings'][security] = {
                    'type': 't bill', 'symbol': None, 'cusip': cusip, 'face_value': face_value, 'quantity': face_value, 'date': account['end_date'], 'total_cost': total_cost,
                    'issue_date': None, 'mature_date': mature_date, 'transactions': []}

    def __trim_lines(self, lines, page_name, start_string=None):
        continued = page_name + (' (continued)')
        trim_blocks = [] 
        # cut lines into page blocks
        while continued in lines:
            # print('found continued: %s: %s' % (page_name, self.statement.pdf_file))
            continues_idx = lines.index(continued)
            trim_block = []
            # add lines till 3 above'INVESTMENT REPORT'
            if 'INVESTMENT REPORT' in lines:
                trim_block = lines[:lines.index('INVESTMENT REPORT')-3]
            else:
                trim_block = lines
            trim_blocks.append(trim_block)
            lines = lines[continues_idx+1:]
        # add lines till 3 above'INVESTMENT REPORT'
        if 'INVESTMENT REPORT' in lines:
            trim_block = lines[:lines.index('INVESTMENT REPORT')-3]
        else:
            trim_block = lines
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

    def __get_symbol_cusip(self, name):
        if len(name) == 9:
            return (None, name)
        return (name, None)
    
    def __get_float(self, text):
        text = text.replace('$', '')
        text = text.replace(',', '')
        try:
            return float(text)
        except:
            return None

    def __set_accounts_info(self):
        for account_number, account_data in self.__name_pages['accounts'].items():
            self.accounts[account_number] = {'statement': self.statement.pdf_file, 'holdings': {}}
            page_num = account_data['Account #']['pages'][0]
            for block in self.statement.get_page_blocks(page_num):
                if block[0].startswith('INVESTMENT REPORT'):
                    dates = block[1].split('-')
                    self.accounts[account_number]['start_date'] = datetime.strptime(dates[0].strip(), '%B %d, %Y')
                    self.accounts[account_number]['end_date'] = datetime.strptime(dates[1].strip(), '%B %d, %Y')
                if block[0].startswith('Account #'):
                    self.accounts[account_number]['type'] = block[1].strip()

    def __set_name_pages(self):
        # search structure:
        # key words under children are the start key words of blocks of lines
        # the 'stop' keyword is the end key word of blocks of those lines
        # the 'lines' feyword has all the lines of that block
        self.__name_pages = {
            'accounts': {},
            'Account #': {
                'pages': [],
                'children': {
                    # Holdings
                    'NH PORTFOLIO 2024 (FIDELITY FUNDS)': {
                        'stop': 'Total Market Value',
                        'lines': [],
                    },
                    'Core Account': {
                        'stop': 'Total Core Account',
                        'lines': [],
                    },
                    'Stock Funds': {
                        'stop': 'Total Stock Funds',
                        'lines': [],
                    },
                    'Equity ETPs': {
                        'stop': 'Total Equity ETPs',
                        'lines': [],
                    },
                    'US Treasury/Agency Securities': {
                        'stop': 'Total US Treasury/Agency',
                        'lines': [],
                    },

                    # Activity
                    'Securities Bought & Sold': {
                        'stop': 'Net Securities Bought & Sold',
                        'lines': [],
                    },
                    'Securities Transferred In': {
                        'stop': 'Total Securities Transferred In',
                        'lines': [],
                    },
                    'Dividends, Interest & Other Income': {
                        'stop': 'Total Dividends, Interest & Other Income',
                        'lines': [],
                    },
                    'Core Fund Activity': {
                        'stop': 'Total Core Fund Activity',
                        'lines': [],
                    },
                    'Exchanges In': {
                        'stop': 'Total Exchanges In',
                        'lines': [],
                    },
                    'Exchanges Out': {
                        'stop': 'Total Exchanges Out',
                        'lines': [],
                    },
                    'Transfers Between Fidelity Accounts': {
                        'stop': 'Total Transfers Between Fidelity Accounts',
                        'lines': [],
                    },
                    'Other Activity Out': {
                        'stop': 'Total Other Activity Out',
                        'lines': [],
                    },
                },
            },
        }
        
        # search for pages that contain the 'Account #' to retrieve account number and their pages
        for page_num, blocks in self.statement.get_blocks().items():
            for block in blocks:
                # print('%s: %s' % (block[0], page_num))
                if block[0].startswith('Account #'):
                    account_number = block[0].split(' # ')[1].strip()
                    if account_number not in self.__name_pages['accounts']:
                        self.__name_pages['accounts'][account_number] = {}
                        self.__name_pages['accounts'][account_number]['Account #'] = copy.deepcopy(self.__name_pages['Account #'])
                    self.__name_pages['accounts'][account_number]['Account #']['pages'].append(page_num)
                    break

        for account_number, account_data in self.__name_pages['accounts'].items():
            # print()
            # print(account_number)
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
        current_activity = 'None'
        for line in lines:
            if line in ['Account Summary', 'Holdings', 'Activity', 'Additional Information and Endnotes']:
                current_activity = line
                # print('activity: %s' % current_activity)
                continue
            if current_name != None:
                if 'stop' in name_pages[current_name]:
                    if line.startswith(name_pages[current_name]['stop']):
                        # print('stop: %s with: %s' % (current_name, line))
                        name_pages[current_name]['lines'] = current_lines
                        current_name = None
                        current_lines = []
                        continue
            
            if current_activity in ['Holdings', 'Activity']:
                if line in name_pages:
                    # HACK for NH
                    if not (line == 'NH PORTFOLIO 2024 (FIDELITY FUNDS)' and current_activity != 'Holdings'):
                        if current_name != None:
                            # print('%s: %s' % (self.name, self.statement.pdf_file))
                            # print('not stopped: %s before start of: %s' % (current_name, line))
                            name_pages[current_name]['lines'] = current_lines
                        # print('\nstart: new: %s old: %s' % (line, current_name))
                        current_name = line
                        current_lines = []
                        continue

            if current_name != None:
                # if current_name == 'Securities Bought & Sold':
                #     print('\t%s' % line)
                current_lines.append(line)
        
        # if 'Holding' is still open that's OK. others raise an exception
        if current_name != None:
            name_pages[current_name]['lines'] = current_lines
            # print('%s: %s' % (self.name, self.statement.pdf_file))
            # print('last current name not stopped: %s' % current_name)
            # raise Exception('last current name not stopped: %s' % current_name)

        for name, name_data in name_pages.items():
            if 'children' in name_data:
                self.__recurse_lines(name_data['children'], name_data['lines'])
