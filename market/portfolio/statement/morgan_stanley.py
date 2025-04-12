from datetime import datetime
from pprint import pp
import math, copy
import pandas as pd

class Morgan_Stanley():
    name = 'Morgan_Stanley'

    def __init__(self, statement):
        self.statement = statement
        self.accounts = {}

        # if self.statement.pdf_file != 'database/statements_ms\\Etrade_TRUST_2024_08.pdf': return
        # if self.statement.pdf_file != 'database/statements_ms\\Etrade_TRUST_2024_12.pdf': return
        # if self.statement.pdf_file != 'database/statements_ms\\Etrade_TRUST_2024_04.pdf': return
        
        # return

        # print('')
        # print('%s: %s' % (self.name, self.statement.pdf_file))

        self.__set_name_pages()
        self.__set_accounts_info()
        self.__set_holdings()
        self.__set_transactions()
        
        # pp(self.__name_pages['accounts'])
        # pp(self.accounts)
        # if self.statement.pdf_file == 'database/statements_ms\\Etrade_TRUST_2024_04.pdf':
        #     pp(self.accounts)

    def __set_transactions(self):
        for account_number, account_data in self.__name_pages['accounts'].items():
            # print(account_number)
            
            if 'Account Detail' in account_data:
                children = account_data['Account Detail']['children']
                
                lines = children['CASH FLOW ACTIVITY BY DATE']['lines']
                if len(lines) > 0:
                    # print('\tCASH FLOW ACTIVITY BY DATE')
                    self.__get_transactions(lines, account_number)
            
                lines = children['TAXABLE INCOME']['lines']
                if len(lines) > 0:
                    # print('\tTAXABLE INCOME')
                    self.__get_transactions(lines, account_number)
            
                lines = children['SECURITY TRANSFERS']['lines']
                if len(lines) > 0:
                    # print('\tSECURITY TRANSFERS')
                    self.__get_transactions(lines, account_number)
            
                lines = children['CORPORATE ACTIONS']['lines']
                if len(lines) > 0:
                    # print('\tCORPORATE ACTIONS')
                    self.__get_transactions(lines, account_number)
            
                # lines = children['UNSETTLED PURCHASES/SALES ACTIVITY']['lines']
                # if len(lines) > 0:
                #     # print('\tUNSETTLED PURCHASES/SALES ACTIVITY')
                #     self.__get_transactions(lines, account_number)
                
                # activities that do nothing on securities, but we keep them around for now
                # ['MONEY MARKET FUND (MMF) AND BANK DEPOSIT PROGRAM ACTIVITY', 'ELECTRONIC TRANSFERS']

            elif 'Activity' in account_data:
                children = account_data['Activity']['children']

                lines = children['SECURITY TRANSFERS']['lines']
                if len(lines) > 0:
                    # print('\tSECURITY TRANSFERS')
                    self.__get_transactions(lines, account_number)

    def __get_transactions(self, lines, account_number):
        account = self.accounts[account_number]
        last_index = None
        current_transaction = {}
        for line_index in range(len(lines)):
            line = lines[line_index]
            line_digits = line.replace('/', '')
            if line_digits.isdigit() and line != line_digits and len(line_digits) <= 4:
                # create a datetime object from the date line
                date_elements = line.split('/')
                date = datetime(month=int(date_elements[0]), day=int(date_elements[1]), year=account['end_date'].year)

                if last_index != None:
                    # check index difference between date line and last date line
                    diff_index = line_index - last_index
                    if diff_index == 1:
                        # looks like we have a Settlement Date
                        current_transaction['settlement_date'] = date
                    else:
                        # we got to the next Transaction Date
                        # store the last one and create a new one
                        self.__parse_transaction(current_transaction)
                        self.__add_transaction(current_transaction, account_number)
                        current_transaction = {'transaction_date': date, 'lines': [], 'statement': self.statement.pdf_file}
                else:
                    # this is the first Transaction Date, create a new one
                    current_transaction = {'transaction_date': date, 'lines': [], 'statement': self.statement.pdf_file}
                
                # set index since last date line
                last_index = line_index
            elif 'transaction_date' in current_transaction:
                current_transaction['lines'].append(line)
        
        # make sure the last transaction is added if needed
        if 'transaction_date' in current_transaction:
            self.__parse_transaction(current_transaction)
            self.__add_transaction(current_transaction, account_number)

    def __add_transaction(self, transaction, account_number):
        # these are all bank transactions
        if transaction['security'] == None: return

        account = self.accounts[account_number]
        security = transaction.pop('security')
        symbol = transaction.pop('symbol')
        cusip = transaction.pop('cusip')
        if security in account['holdings']:
            account['holdings'][security]['transactions'].append(transaction)
        else:
            account['holdings'][security] = {'type': None, 'symbol': symbol, 'cusip': cusip, 'date': account['end_date'], 'transactions': []}
            account['holdings'][security]['transactions'].append(transaction)

    def __parse_transaction(self, transaction):
        lines = transaction.pop('lines')
        lines = self.__trim_transaction_lines(lines)
        transaction['type'] = lines[0]
        # print('\t\t%s' % transaction['type'])
        # return
        transaction['security'] = lines[1]
        transaction['symbol'] = None
        transaction['cusip'] = None
        if transaction['type'] in ['Bought', 'Sold', 'Dividend Reinvestment', 'Redemption']:
            transaction['comments'] = ' '.join(lines[2:-3])
            transaction['quantity'] = self.__get_float(lines[-3])
            if transaction['type'] in ['Sold', 'Redemption'] and transaction['quantity'] != None:
                transaction['quantity'] = -transaction['quantity']
            transaction['price'] = self.__get_float(lines[-2])
        elif transaction['type'] in ['Dividend', 'Qualified Dividend', 'LT Cap Gain Distribution', 'ST Cap Gain Distribution', 'Service Fee']:
            transaction['comments'] = ' '.join(lines[2:-1])
            transaction['amount'] = self.__get_float(lines[-1])
        elif transaction['type'] in ['Transfer into Account', 'Transfer out of Account']:
            transaction['comments'] = ' '.join(lines[2:-2])
            transaction['quantity'] = self.__get_float(lines[-2])
            if transaction['type'] == 'Transfer out of Account' and transaction['quantity'] != None:
                transaction['quantity'] = -transaction['quantity']
            transaction['amount'] = self.__get_float(lines[-1])
        elif transaction['type'] in ['Exchange Delivered Out', 'Exchange Received In', 'Stock Spin-Off']:
            transaction['comments'] = ' '.join(lines[2:-1])
            transaction['quantity'] = self.__get_float(lines[-1])
        elif transaction['type'] == 'Interest Income' and not 'BANK' in transaction['security']:
            transaction['comments'] = ' '.join(lines[2:-1])
            transaction['amount'] = self.__get_float(lines[-1])
        else:
            # we are drastic, clear transaction of it does not effect equity
            transaction['security'] = None
            return
        
        # add cusip codes to security if needed
        if transaction['security'] in ['UNITED STATES TREASURY BILL', 'JPMORGAN CHASE BK N A FID']:
            cusip = transaction['comments'].split(' [')[1].split(']')[0]
            transaction['security'] += ' ' + cusip
            transaction['cusip'] = cusip
            if 'price' in transaction:
                transaction['price'] = transaction['price'] / 100.0

        # pp(transaction)

    def __trim_transaction_lines(self, lines):
        if 'Account Detail' in lines:
            # print('trim: Account Detail')
            return lines[:lines.index('Account Detail')]
        return lines

    def __set_holdings(self):
        for account_number, account_data in self.__name_pages['accounts'].items():
            # print(account_number)
            
            if 'Account Detail' in account_data:
                children = account_data['Account Detail']['children']

                lines = children['COMMON STOCKS']['lines']
                if len(lines) > 0:
                    # print('\tCOMMON STOCKS')
                    self.__add_stock(lines, account_number,'stock')

                lines = children['OPEN-END MUTUAL FUNDS']['lines']
                if len(lines) > 0:
                    # print('\tOPEN-END MUTUAL FUNDS')
                    self.__add_stock(lines, account_number, 'mutual fund')

                lines = children['OPEN-END NON-SWEEP MONEY MARKET FUNDS']['lines']
                if len(lines) > 0:
                    # print('\tOPEN-END NON-SWEEP MONEY MARKET FUNDS')
                    self.__add_stock(lines, account_number, 'money market fund')

                lines = children['EXCHANGE-TRADED & CLOSED-END FUNDS']['lines']
                if len(lines) > 0:
                    # print('\tEXCHANGE-TRADED & CLOSED-END FUNDS')
                    self.__add_stock(lines, account_number, 'etf')

                lines = children['TREASURY SECURITIES']['lines']
                if len(lines) > 0:
                    # print('\tTREASURY SECURITIES')
                    self.__add_bill(lines, account_number, 't bill')

                lines = children['CERTIFICATES OF DEPOSIT']['lines']
                if len(lines) > 0:
                    # print('\tCERTIFICATES OF DEPOSIT')
                    self.__add_bill(lines, account_number, 'cd')
            elif 'Holdings' in account_data:
                children = account_data['Holdings']['children']

                lines = children['COMMON STOCKS']['lines']
                if len(lines) > 0:
                    # print('\tCOMMON STOCKS')
                    self.__add_stock(lines, account_number, 'stock')

    def __add_bill(self, lines, account_number, bill_type):
        # add bill data to account holdings
        account = self.accounts[account_number]
        holding_values = lines[lines.index('Security Description')+1:lines.index('Yield %')+1]
        lines = lines[lines.index('Yield %')+1:]

        security = None
        for line_idx in range(len(lines)):
            line = lines[line_idx]
            if line.isupper():
                if not 'CUSIP' in lines[line_idx+1]: continue
                details = lines[line_idx+1].split(';')
                # cusip = lines[line_idx+1].split('CUSIP')[1].strip()
                cusip = details[2].strip().split(' ')[1].strip()
                symbol, cusip = self.__get_symbol_cusip(cusip)
                mature_date = details[1].strip().split(' ')[1].strip()
                security = line + ' ' + cusip
                account['holdings'][security] = {'type': bill_type, 'symbol': symbol, 'cusip': cusip, 'date': account['end_date'], 'transactions': []}
                holding_lines = lines[line_idx+2:line_idx+len(holding_values)+2]
                account['holdings'][security]['face_value'] = self.__get_float(holding_lines[holding_values.index('Face Value')])
                account['holdings'][security]['quantity'] = account['holdings'][security]['face_value']
                account['holdings'][security]['total_cost'] = self.__get_float(holding_lines[holding_values.index('Orig Total Cost')])
                if bill_type == 'cd':
                    account['holdings'][security]['rate'] = self.__get_float(details[0].split('  ')[1].strip().rstrip('%'))
                account['holdings'][security]['mature_date'] = datetime.strptime(mature_date, '%m/%d/%Y')
            elif bill_type == 't bill' and line.startswith('Issued'):
                issue_date = line.split(';')[0].split(' ')[1].strip()
                account['holdings'][security]['issue_date'] = datetime.strptime(issue_date, '%m/%d/%y')
            elif bill_type == 'cd' and line.startswith('Interest Paid at Maturity'):
                splits = line.split(';')
                for split in splits[1:]:
                    split = split.strip()
                    if split.startswith('Issued'):
                        issue_date = split.split(' ')[1].strip()
                        account['holdings'][security]['issue_date'] = datetime.strptime(issue_date, '%m/%d/%y')

    def __add_stock(self, lines, account_number, stock_type):
        # add stock data to account holdings
        account = self.accounts[account_number]
        holding_values = lines[lines.index('Security Description')+1:lines.index('Yield %')+1]
        lines = lines[lines.index('Yield %')+1:]
        for line_idx in range(len(lines)):
            line = lines[line_idx]
            if line.isupper() and ' (' in line:
                splits = line.split(' (')
                security = splits[0]
                symbol, cusip = self.__get_symbol_cusip(splits[1][:-1])
                account['holdings'][security] = {'type': stock_type, 'symbol': symbol, 'cusip': cusip, 'date': account['end_date'], 'transactions': []}
                if lines[line_idx+1] == 'Purchases':
                    holding_lines = lines[line_idx+1:]
                    holding_lines = holding_lines[holding_lines.index('Total')+1:]
                    account['holdings'][security]['quantity'] = self.__get_float(holding_lines[holding_values.index('Quantity')])
                    account['holdings'][security]['total_cost'] = self.__get_float(holding_lines[holding_values.index('Total Cost')-1])
                else:
                    holding_lines = lines[line_idx+1:line_idx+len(holding_values)+1]
                    account['holdings'][security]['quantity'] = self.__get_float(holding_lines[holding_values.index('Quantity')])
                    account['holdings'][security]['total_cost'] = self.__get_float(holding_lines[holding_values.index('Total Cost')])
                if stock_type == 'money market fund':
                    account['holdings'][security]['total_cost'] = account['holdings'][security]['quantity']

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
            
            if 'Account Detail' in account_data:
                self.accounts[account_number] = {'statement': self.statement.pdf_file, 'holdings': {}}
                blocks = self.statement.get_page_blocks(account_data['Account Detail']['pages'][0])
                self.accounts[account_number]['type'] = blocks[2][0].strip()
                period = blocks[1][0].split('For the Period ')[-1].strip()
                self.accounts[account_number]['start_date'], self.accounts[account_number]['end_date'] = self.__get_dates(period)
            else:
                page_name = None
                if 'Holdings' in account_data: page_name = 'Holdings'
                elif 'Activity' in account_data: page_name = 'Activity'
                if page_name != None:
                    self.accounts[account_number] = {'statement': self.statement.pdf_file, 'holdings': {}}
                    blocks = self.statement.get_page_blocks(account_data[page_name]['pages'][0])
                    for block_idx in range(len(blocks)):
                        block = blocks[block_idx]
                        if block[0].startswith('CLIENT STATEMENT'):
                            period = block[0].split('For the Period')[1].strip()
                            self.accounts[account_number]['start_date'], self.accounts[account_number]['end_date'] = self.__get_dates(period)
                        if block[0].startswith('Page '):
                            self.accounts[account_number]['type'] = blocks[block_idx-2][0].strip()

    def __get_dates(self, period):
        # change one line period string to start and end dates
        splits = period.split(',')
        period = splits[0].strip()
        year = splits[1].strip()
        if '- ' in period:
            splits = period.split('-')
            start_date = splits[0].strip()+ ' ' + year
            end_date = splits[1].strip()+ ' ' + year
        else:
            splits = period.split('-')
            end_day = splits[1].strip()
            start_date = splits[0].strip()+ ' ' + year
            end_date = start_date.split(' ')[0].strip()+ ' ' + splits[1].strip() + ' ' + year
        start_date = datetime.strptime(start_date, '%B %d %Y')
        end_date = datetime.strptime(end_date, '%B %d %Y')
        return (start_date, end_date)

    def __set_name_pages(self):
        # search structure:
        # key words under children are the start key words of blocks of lines
        # the 'stop' keyword is the end key word of blocks of those lines
        # the 'lines' feyword has all the lines of that block
        self.__name_pages = {
            'accounts': {},
            'Account Detail': {
                'pages': [],
                'children': {
                    # 'HOLDINGS'
                    'COMMON STOCKS': {
                        'stop': 'STOCKS',
                        'lines': [],
                    },
                    'OPEN-END MUTUAL FUNDS': {
                        'stop': 'MUTUAL FUNDS',
                        'lines': [],
                    },
                    'OPEN-END NON-SWEEP MONEY MARKET FUNDS': {
                        'stop': 'MUTUAL FUNDS',
                        'lines': [],
                    },
                    'EXCHANGE-TRADED & CLOSED-END FUNDS': {
                        'stop': 'EXCHANGE-TRADED & CLOSED-END FUNDS',
                        'lines': [],
                    },
                    'TREASURY SECURITIES': {
                        'stop': 'GOVERNMENT SECURITIES',
                        'lines': [],
                    },
                    'CERTIFICATES OF DEPOSIT': {
                        'stop': 'CERTIFICATES OF DEPOSIT',
                        'lines': [],
                    },

                    # 'ACTIVITY'
                    'CASH FLOW ACTIVITY BY DATE': {
                        'stop': 'NET CREDITS/(DEBITS)',
                        'lines': [],
                    },
                    'MONEY MARKET FUND (MMF) AND BANK DEPOSIT PROGRAM ACTIVITY': {
                        'stop': 'NET ACTIVITY FOR PERIOD',
                        'lines': [],
                    },
                    'TAXABLE INCOME': {
                        'stop': 'TOTAL TAXABLE INCOME',
                        'lines': [],
                    },
                    'ELECTRONIC TRANSFERS': {
                        'stop': 'TOTAL ELECTRONIC TRANSFERS',
                        'lines': [],
                    },
                    'OTHER CREDITS AND DEBITS': {
                        'stop': 'TOTAL OTHER CREDITS AND DEBITS',
                        'lines': [],
                    },
                    'SECURITY TRANSFERS': {
                        'stop': 'TOTAL SECURITY TRANSFERS',
                        'lines': [],
                    },
                    'CORPORATE ACTIONS': {
                        'stop': None,
                        'lines': [],
                    },
                    'UNSETTLED PURCHASES/SALES ACTIVITY': {
                        'stop': 'NET UNSETTLED PURCHASES/SALES',
                        'lines': [],
                    },
                    'MESSAGES': {
                        'stop': 'CLIENT STATEMENT',
                        'lines': [],
                    },
                },
            },
            'Holdings': {
                'pages': [],
                'children': {
                    'COMMON STOCKS': {
                        'stop': 'STOCKS',
                        'lines': [],
                    },
                },
            },
            'Activity': {
                'pages': [],
                'children': {
                    'SECURITY TRANSFERS': {
                        'stop': '066058 MSGDD46B', # HACK only one occasion
                        'lines': [],
                    },
                },
            },
        }

        # search for pages that contain the 'Account Detail' or 'Holdings' and 'Activity' to retrieve account number and their pages
        for page_num, blocks in self.statement.get_blocks().items():
            # find pages for sections
            for block in blocks:
                if block[0] == 'Account Detail':
                    # found 'Account Detail' page
                    blocks = self.statement.get_page_blocks(page_num)
                    # get account number
                    account_number = blocks[3][0].strip()
                    if account_number not in self.__name_pages['accounts']:
                        # create account number if needed
                        self.__name_pages['accounts'][account_number] = {}
                        self.__name_pages['accounts'][account_number]['Account Detail'] = copy.deepcopy(self.__name_pages['Account Detail'])
                    # add page number to account
                    self.__name_pages['accounts'][account_number]['Account Detail']['pages'].append(page_num)
                    # once in page is enough
                    break
                if block[0] == 'Holdings' or block[0] == 'Activity':
                    # found 'Holdings' or 'Activity' page
                    pages_name = block[0]
                    blocks = self.statement.get_page_blocks(page_num)
                    for block_idx in range(len(blocks)):
                        block = blocks[block_idx]
                        # find 'Page ' line, now we can index for account number
                        if block[0].startswith('Page '):
                            account_number = blocks[block_idx-1][0].strip()
                            if account_number not in self.__name_pages['accounts']:
                                # create account number if needed
                                self.__name_pages['accounts'][account_number] = {}
                            if not pages_name in self.__name_pages['accounts'][account_number]:
                                self.__name_pages['accounts'][account_number][pages_name] = copy.deepcopy(self.__name_pages[pages_name])
                            # add page number to account
                            self.__name_pages['accounts'][account_number][pages_name]['pages'].append(page_num)
                    # once in page is enough
                    break
        
        for account_number, account_data in self.__name_pages['accounts'].items():
            for pages_name, page_data in account_data.items():
                if len(page_data['pages']) > 0:
                    if len(page_data['children']) > 0:
                        lines = []
                        for page_num in page_data['pages']:
                            blocks = self.statement.get_page_blocks(page_num)
                            for block in blocks:
                                # # TODO fix continued like in etrade, seems only in activity
                                # for line in block:
                                #     if 'CONTINUED' in line:
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
                        # print('stop: %s with: %s' % (current_name, line))
                        name_pages[current_name]['lines'] = current_lines
                        current_name = None
                        current_lines = []
                        continue
            
            if line in name_pages.keys():
                if current_name != None:
                    # print('not stopped: %s before start of: %s' % (current_name, line))
                    # print('stop: %s with: %s' % (current_name, line))
                    name_pages[current_name]['lines'] = current_lines
                # print('start: new: %s old: %s' % (line, current_name))
                current_name = line
                current_lines = []
                continue

            if current_name != None:
                current_lines.append(line)

        if current_name != None and current_name != 'MESSAGES':
            # print('stop: %s with: %s' % (current_name, line))
            name_pages[current_name]['lines'] = current_lines
            # raise Exception('last current name not stopped: %s' % current_name)
            # print('%s: %s' % (self.name, self.statement.pdf_file))
            # print('last current name not stopped: %s' % current_name)
            # for line in current_lines:
            #     print('\t%s' % line)

        for name, name_data in name_pages.items():
            if 'children' in name_data:
                self.__recurse_lines(name_data['children'], name_data['lines'])
