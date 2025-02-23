from datetime import datetime
from pprint import pp
import math
import pandas as pd

class Morgan_Stanley():
    name = 'Morgan_Stanley'

    def __init__(self, statement):
        self.statement = statement
        self.accounts = {}
        return

        # print('')
        # print('%s: %s' % (self.name, self.statement.pdf_file))

        self.__set_name_pages()
        self.__set_accounts_info()
        self.__set_holdings()
        self.__set_transactions()

        # pp(self.accounts)

    def __set_transactions(self):
        # TODO: Maybe pop lines after using them ?

        activity = self.__name_pages['Account Detail']['children']['ACTIVITY']['children']
        self.__get_transactions(activity['CASH FLOW ACTIVITY BY DATE']['lines'])
        self.__get_transactions(activity['INVESTMENT RELATED ACTIVITY']['children']['TAXABLE INCOME']['lines'])
        self.__get_transactions(activity['TRANSFERS, CORPORATE ACTIONS AND ADDITIONAL ACTIVITY']['children']['SECURITY TRANSFERS']['lines'])
        self.__get_transactions(activity['TRANSFERS, CORPORATE ACTIONS AND ADDITIONAL ACTIVITY']['children']['CORPORATE ACTIONS']['lines'])
        self.__get_transactions(activity['UNSETTLED PURCHASES/SALES ACTIVITY']['lines'])
        
        # activities that do nothing on securities, but we keep them around for now
        # self.__get_transactions(activity['MONEY MARKET FUND (MMF) AND BANK DEPOSIT PROGRAM ACTIVITY']['lines'])
        # self.__get_transactions(activity['CASH RELATED ACTIVITY']['children']['ELECTRONIC TRANSFERS']['lines'])
        

        activity = self.__name_pages['Activity']['children']
        self.__get_transactions(activity['SECURITY ACTIVITY']['children']['SECURITY TRANSFERS']['lines'])

        # activities that do nothing on securities, but we keep them around for now
        # self.__get_transactions(activity['CASH RELATED ACTIVITY']['children']['ELECTRONIC TRANSFERS']['lines'])

    def __get_transactions(self, lines):
        account = self.accounts[list(self.accounts.keys())[0]]
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
                        self.__add_transaction(current_transaction)
                        current_transaction = {'transaction_date': date, 'lines': []}
                else:
                    # this is the first Transaction Date, create a new one
                    current_transaction = {'transaction_date': date, 'lines': []}
                
                # set index since last date line
                last_index = line_index
            elif 'transaction_date' in current_transaction:
                current_transaction['lines'].append(line)
        
        # make sure the last transaction is added if needed
        if 'transaction_date' in current_transaction:
            self.__parse_transaction(current_transaction)
            self.__add_transaction(current_transaction)

    def __add_transaction(self, transaction):
        if transaction['security'] == None: return
        account = self.accounts[list(self.accounts.keys())[0]]
        security = transaction.pop('security')
        if security in account['holdings']:
            account['holdings'][security]['transactions'].append(transaction)
        else:
            account['holdings'][security] = {'type': None, 'symbol': None, 'date': account['end_date'], 'transactions': []}
            account['holdings'][security]['transactions'].append(transaction)

    def __parse_transaction(self, transaction):
        lines = transaction.pop('lines')
        lines = self.__trim_transaction_lines(lines)
        transaction['type'] = lines[0]
        transaction['security'] = lines[1]
        if transaction['type'] in ['Bought', 'Sold', 'Dividend Reinvestment', 'Redemption']:
            transaction['comments'] = ' '.join(lines[2:-3])
            transaction['quantity'] = self.__get_float(lines[-3])
            transaction['price'] = self.__get_float(lines[-2])
        elif transaction['type'] in ['Dividend', 'Qualified Dividend', 'LT Cap Gain Distribution', 'ST Cap Gain Distribution', 'Service Fee']:
            transaction['comments'] = ' '.join(lines[2:-1])
            transaction['amount'] = self.__get_float(lines[-1])
        elif transaction['type'] in ['Transfer into Account', 'Transfer out of Account']:
            transaction['comments'] = ' '.join(lines[2:-2])
            transaction['quantity'] = self.__get_float(lines[-2])
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
            transaction['symbol'] = cusip

        # pp(transaction)

    def __trim_transaction_lines(self, lines):
        if 'Account Detail' in lines:
            return lines[:lines.index('Account Detail')]
        return lines

    def __set_holdings(self):
        # 'Account Detail' 'HOLDINGS'
        holding = self.__name_pages['Account Detail']['children']['HOLDINGS']['children']

        lines = holding['STOCKS']['children']['COMMON STOCKS']['lines']
        if len(lines) > 0:
            # print('\tCOMMON STOCKS')
            self.__add_stock(lines, 'stock')

        lines = holding['EXCHANGE-TRADED & CLOSED-END FUNDS']['lines']
        if len(lines) > 0:
            # print('\tEXCHANGE-TRADED & CLOSED-END FUNDS')
            self.__add_stock(lines, 'etf')

        lines = holding['MUTUAL FUNDS']['children']['OPEN-END MUTUAL FUNDS']['lines']
        if len(lines) > 0:
            # print('\tOPEN-END MUTUAL FUNDS')
            self.__add_stock(lines, 'mutual fund')
        
        lines = holding['MUTUAL FUNDS']['children']['OPEN-END NON-SWEEP MONEY MARKET FUNDS']['lines']
        if len(lines) > 0:
            # print('\tOPEN-END NON-SWEEP MONEY MARKET FUNDS')
            self.__add_stock(lines, 'money market fund')
        
        lines = holding['GOVERNMENT SECURITIES']['children']['TREASURY SECURITIES']['lines']
        if len(lines) > 0:
            # print('\tTREASURY SECURITIES')
            self.__add_bill(lines, 't bill')
        
        lines = holding['CERTIFICATES OF DEPOSIT']['lines']
        if len(lines) > 0:
            # print('\tCERTIFICATES OF DEPOSIT')
            self.__add_bill(lines, 'cd')
        
        # 'Holdings'
        holding = self.__name_pages['Holdings']['children']

        lines = holding['STOCKS']['children']['COMMON STOCKS']['lines']
        if len(lines) > 0:
            # print('\tCOMMON STOCKS')
            self.__add_stock(lines, 'stock')

    def __add_bill(self, lines, bill_type):
        # add bill data to account holdings
        account = self.accounts[list(self.accounts.keys())[0]]
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
                mature_date = details[1].strip().split(' ')[1].strip()
                security = line + ' ' + cusip
                account['holdings'][security] = {'type': bill_type, 'symbol': cusip, 'date': account['end_date'], 'transactions': []}
                holding_lines = lines[line_idx+2:line_idx+len(holding_values)+2]
                account['holdings'][security]['face_value'] = self.__get_float(holding_lines[holding_values.index('Face Value')])
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

    def __add_stock(self, lines, stock_type):
        # add stock data to account holdings
        account = self.accounts[list(self.accounts.keys())[0]]
        holding_values = lines[lines.index('Security Description')+1:lines.index('Yield %')+1]
        lines = lines[lines.index('Yield %')+1:]
        for line_idx in range(len(lines)):
            line = lines[line_idx]
            if line.isupper() and ' (' in line:
                splits = line.split(' (')
                security = splits[0]
                account['holdings'][security] = {'type': stock_type, 'symbol': splits[1][:-1], 'date': account['end_date'], 'transactions': []}
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

    def __get_float(self, text):
        if text.startswith('$'): text = text[1:]
        if text.startswith('('): text = '-'+text[1:-1]
        text = text.replace(',', '')
        try:
            return float(text)
        except:
            return None

    def __set_accounts_info(self):
        account_type = None
        account_number = None
        start_date = None
        end_date = None

        # get account info
        lines = self.statement.get_page_lines(self.__name_pages['Account Summary']['pages'][0])
        for line_idx in range(len(lines)):
            line = lines[line_idx]
            if account_type == None and 'Account' in line:
                account_type = line
                account_number = lines[line_idx+1]
            if 'For the Period' in line:
                period = line.split('For the Period ')[-1].strip()
                splits = period.split(',')
                year = splits[1].strip()
                splits = splits[0].split('-')
                
                start_date = splits[0].strip().split(' ')

                end_date = splits[1].strip().split(' ')
                if len(end_date) > 1:
                    end_date = '%s/%s/%s' % (end_date[0].strip(), end_date[1].strip(), year)
                else:
                    end_date = '%s/%s/%s' % (start_date[0].strip(), end_date[0].strip(), year)
                end_date = datetime.strptime(end_date, '%B/%d/%Y')

                start_date = '%s/%s/%s' % (start_date[0].strip(), start_date[1].strip(), year)
                start_date = datetime.strptime(start_date, '%B/%d/%Y')
        self.accounts[account_number] = {
            'type': account_type,
            'start_date': start_date,
            'end_date': end_date,
            'holdings': {},
        }

    def __set_name_pages(self):
        self.__name_pages = {
            'Research Ratings & GIMA Status Definitions': {
                'pages': [],
                'children': {},
            },
            'Expanded Disclosures': {
                'pages': [],
                'children': {},
            },
            'Account Summary': {
                'pages': [],
                'children': {},
            },
            'Account Detail': {
                'pages': [],
                'children': {
                    'HOLDINGS': {
                        'stop': None,
                        'lines': [],
                        'children': {
                            'STOCKS': {
                                'stop': 'STOCKS',
                                'lines': [],
                                'children': {
                                    'COMMON STOCKS': {
                                        'stop': None,
                                        'lines': [],
                                    },
                                },
                            },
                            'MUTUAL FUNDS': {
                                'stop': 'MUTUAL FUNDS',
                                'lines': [],
                                'children': {
                                    'OPEN-END MUTUAL FUNDS': {
                                        'stop': None,
                                        'lines': [],
                                    },
                                    'OPEN-END NON-SWEEP MONEY MARKET FUNDS': {
                                        'stop': None,
                                        'lines': [],
                                    },
                                },
                            },
                            'EXCHANGE-TRADED & CLOSED-END FUNDS': {
                                'stop': 'EXCHANGE-TRADED & CLOSED-END FUNDS',
                                'lines': [],
                            },
                            'GOVERNMENT SECURITIES': {
                                'stop': 'GOVERNMENT SECURITIES',
                                'lines': [],
                                'children': {
                                    'TREASURY SECURITIES': {
                                        'stop': None,
                                        'lines': [],
                                    },
                                },
                            },
                            'CERTIFICATES OF DEPOSIT': {
                                'stop': 'CERTIFICATES OF DEPOSIT',
                                'lines': [],
                            },
                            'EXCHANGE-TRADED & CLOSED-END FUNDS': {
                                'stop': 'EXCHANGE-TRADED & CLOSED-END FUNDS',
                                'lines': [],
                            },
                        },
                    },
                    'ACTIVITY': {
                        'stop': None,
                        'lines': [],
                        'children': {
                            'CASH FLOW ACTIVITY BY DATE': {
                                'stop': 'NET CREDITS/(DEBITS)',
                                'lines': [],
                            },
                            'MONEY MARKET FUND (MMF) AND BANK DEPOSIT PROGRAM ACTIVITY': {
                                'stop': 'NET ACTIVITY FOR PERIOD',
                                'lines': [],
                            },
                            'INVESTMENT RELATED ACTIVITY': {
                                'stop': None,
                                'lines': [],
                                'children': {
                                    'TAXABLE INCOME': {
                                        'stop': 'TOTAL TAXABLE INCOME',
                                        'lines': [],
                                    },
                                },
                            },
                            'CASH RELATED ACTIVITY': {
                                'stop': None,
                                'lines': [],
                                'children': {
                                    'ELECTRONIC TRANSFERS': {
                                        'stop': 'TOTAL ELECTRONIC TRANSFERS',
                                        'lines': [],
                                    },
                                    'OTHER CREDITS AND DEBITS': {
                                        'stop': 'TOTAL OTHER CREDITS AND DEBITS',
                                        'lines': [],
                                    },
                                },
                            },
                            'TRANSFERS, CORPORATE ACTIONS AND ADDITIONAL ACTIVITY': {
                                'stop': None,
                                'lines': [],
                                'children': {
                                    'SECURITY TRANSFERS': {
                                        'stop': 'TOTAL SECURITY TRANSFERS',
                                        'lines': [],
                                    },
                                    'CORPORATE ACTIONS': {
                                        'stop': None,
                                        'lines': [],
                                    },
                                },
                            },
                            'UNSETTLED PURCHASES/SALES ACTIVITY': {
                                'stop': 'NET UNSETTLED PURCHASES/SALES',
                                'lines': [],
                            },
                        },
                    },
                    'MESSAGES': {
                        'stop': None,
                        'lines': [],
                    },
                },
            },
            'Holdings': {
                'pages': [],
                'children': {
                    'CASH, DEPOSITS AND MONEY MARKET FUNDS': {
                        'stop': 'CASH, DEPOSITS AND MONEY MARKET FUNDS',
                        'lines': [],
                    },
                    'STOCKS': {
                        'stop': 'STOCKS',
                        'lines': [],
                        'children': {
                            'COMMON STOCKS': {
                                'stop': None,
                                'lines': [],
                            },
                        },
                    },
                },
            },
            'Activity': {
                'pages': [],
                'children': {
                    'CASH RELATED ACTIVITY': {
                        'stop': None,
                        'lines': [],
                        'children': {
                            'ELECTRONIC TRANSFERS': {
                                'stop': 'TOTAL ELECTRONIC TRANSFERS',
                                'lines': [],
                            },
                        },
                    },
                    'SECURITY ACTIVITY': {
                        'stop': None,
                        'lines': [],
                        'children': {
                            'SECURITY TRANSFERS': {
                                'stop': '066058 MSGDD46B', # NOTE: this is very hacky , but only one occasion
                                'lines': [],
                            },
                        },
                    },
                },
            },
            'Messages': {
                'pages': [],
                'children': {},
            },
            'Research Ratings Definitions': {
                'pages': [],
                'children': {},
            },
            'Standard Disclosures': {
                'pages': [],
                'children': {},
            },
            'Disclosure': {
                'pages': [],
                'children': {},
            },
            'Recap of Cash Management Activity': {
                'pages': [],
                'children': {},
            },
        }
        for page_num, blocks in self.statement.get_blocks().items():
            for block in blocks:
                if block[0] in self.__name_pages.keys():
                    # print('%s: %s' % (block[0], page_num))
                    self.__name_pages[block[0]]['pages'].append(page_num)
                    break
                if 'Recap of Cash Management Activity' in block[0]:
                    # print('Recap of Cash Management Activity: %s' % page_num)
                    self.__name_pages['Recap of Cash Management Activity']['pages'].append(page_num)
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
                self.__recurse_lines(name_data['children'], name_data['lines'])
