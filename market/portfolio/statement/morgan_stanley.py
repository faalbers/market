from datetime import datetime
from pprint import pp
import math
import pandas as pd

class Morgan_Stanley():
    name = 'Morgan_Stanley'

    def __init__(self, statement):
        self.statement = statement

        print('')
        print('%s: %s' % (self.name, self.statement.pdf_file))

        self.__set_account_info()
        self.__set_holdings()
        self.__set_transactions()
        
        print('Account Number: %s' % self.account_number)
        print('Account Type  : %s' % self.account_type)
        print('Start Date    : %s' % self.start_date)
        print('End Date      : %s' % self.end_date)

        # pp(self.holdings)
        pp(self.transactions)
    
    def __set_holdings(self):
        self.holdings = {}
        
        # 'Holdings'
        holding = self.__name_pages['Holdings']['children']
        for line in holding['STOCKS']['children']['COMMON STOCKS']['lines']:
            if line.isupper() and ' (' in line:
                splits = line.split(' (')
                self.holdings[splits[0]] = {'type': 'STOCK', 'symbol': splits[1][:-1]}

        # 'Account Detail' 'HOLDINGS'
        holding = self.__name_pages['Account Detail']['children']['HOLDINGS']['children']

        # securities symbols
        for line in holding['STOCKS']['children']['COMMON STOCKS']['lines']:
            if line.isupper() and ' (' in line:
                splits = line.split(' (')
                self.holdings[splits[0]] = {'type': 'STOCK', 'symbol': splits[1][:-1]}
        mutual_funds = holding['MUTUAL FUNDS']['children']
        for line in mutual_funds['OPEN-END MUTUAL FUNDS']['lines']:
            if line.isupper() and ' (' in line:
                splits = line.split(' (')
                self.holdings[splits[0]] = {'type': 'MUTUAL FUND', 'symbol': splits[1][:-1]}
        for line in mutual_funds['OPEN-END NON-SWEEP MONEY MARKET FUNDS']['lines']:
            if line.isupper() and ' (' in line:
                splits = line.split(' (')
                self.holdings[splits[0]] = {'type': 'MONEY MARKET FUND', 'symbol': splits[1][:-1]}
        for line in holding['EXCHANGE-TRADED & CLOSED-END FUNDS']['lines']:
            if line.isupper() and ' (' in line:
                splits = line.split(' (')
                self.holdings[splits[0]] = {'type': 'EXCHANGE-TRADED FUND', 'symbol': splits[1][:-1]}

        # securities cusip
        treasaury_lines = holding['GOVERNMENT SECURITIES']['children']['TREASURY SECURITIES']['lines']
        for line_index in range(len(treasaury_lines)):
            line = treasaury_lines[line_index]
            if line.isupper():
                if (len(treasaury_lines)-line_index) > 1:
                    next_line = treasaury_lines[line_index+1]
                    if 'CUSIP' in next_line:
                        cusip = next_line.split('CUSIP ')[1].strip()
                        self.holdings[line+' '+cusip] = {'type': 'TREASURY BILL', 'symbol': cusip}
        certificate_lines = holding['CERTIFICATES OF DEPOSIT']['lines']
        for line_index in range(len(certificate_lines)):
            line = certificate_lines[line_index]
            if line.isupper():
                if (len(certificate_lines)-line_index) > 1:
                    next_line = certificate_lines[line_index+1]
                    if 'CUSIP' in next_line:
                        cusip = next_line.split('CUSIP ')[1].strip()
                        self.holdings[line+' '+cusip] = {'type': 'CERTIFICATE OF DEPOSIT', 'symbol': cusip}

    def __set_transactions(self):
        self.transactions = []

        # TODO: Maybe pop lines after using them ?

        activity = self.__name_pages['Activity']['children']
        self.__get_transactions(activity['CASH RELATED ACTIVITY']['children']['ELECTRONIC TRANSFERS']['lines'])
        self.__get_transactions(activity['SECURITY ACTIVITY']['children']['SECURITY TRANSFERS']['lines'])

        activity = self.__name_pages['Account Detail']['children']['ACTIVITY']['children']
        self.__get_transactions(activity['CASH FLOW ACTIVITY BY DATE']['lines'])
        self.__get_transactions(activity['MONEY MARKET FUND (MMF) AND BANK DEPOSIT PROGRAM ACTIVITY']['lines'])
        self.__get_transactions(activity['INVESTMENT RELATED ACTIVITY']['children']['TAXABLE INCOME']['lines'])
        self.__get_transactions(activity['CASH RELATED ACTIVITY']['children']['ELECTRONIC TRANSFERS']['lines'])
        self.__get_transactions(activity['TRANSFERS, CORPORATE ACTIONS AND ADDITIONAL ACTIVITY']['children']['SECURITY TRANSFERS']['lines'])
        self.__get_transactions(activity['TRANSFERS, CORPORATE ACTIONS AND ADDITIONAL ACTIVITY']['children']['CORPORATE ACTIONS']['lines'])
        self.__get_transactions(activity['UNSETTLED PURCHASES/SALES ACTIVITY']['lines'])

    def __get_transactions(self, lines):
        last_index = None
        current_transaction = {}
        for line_index in range(len(lines)):
            line = lines[line_index]
            line_digits = line.replace('/', '')
            if line_digits.isdigit() and line != line_digits and len(line_digits) <= 4:
                # create a datetime object from the date line
                date_elements = line.split('/')
                date = datetime(month=int(date_elements[0]), day=int(date_elements[1]), year=self.end_date.year)

                if last_index != None:
                    # check index difference between date line and last date line
                    diff_index = line_index - last_index
                    if diff_index == 1:
                        # looks like we have a Settlement Date
                        current_transaction['SettlementDate'] = date
                    else:
                        # we got to the next Transaction Date
                        # store the last one and create a new one
                        self.__parse_transaction(current_transaction)
                        self.transactions.append(current_transaction)
                        current_transaction = {'TransactionDate': date, 'lines': []}
                else:
                    # this is the first Transaction Date, create a new one
                    current_transaction = {'TransactionDate': date, 'lines': []}
                
                # set index since last date line
                last_index = line_index
            elif 'TransactionDate' in current_transaction:
                current_transaction['lines'].append(line)
        
        # make sure the last transaction is added if needed
        if 'TransactionDate' in current_transaction:
            # trim lines if needed
            self.__parse_transaction(current_transaction)
            self.transactions.append(current_transaction)

    def __parse_transaction(self, transaction):
        lines = transaction.pop('lines')
        last_string_index = self.__get_last_string_index(lines)
        transaction['TransactionType'] = lines[0]
        transaction['Description'] = lines[1]
        if transaction['Description'] in self.holdings:
            transaction['Symbol'] = self.holdings[transaction['Description']]['symbol']
            transaction['SecurityType'] = self.holdings[transaction['Description']]['type']
        transaction['Comments'] = ' '.join(lines[2:(last_string_index+1)])
        # NOTE: this is a hack
        if transaction['Description'] == 'UNITED STATES TREASURY BILL':
            cusip = transaction['Comments'].split(' [')[1].split(']')[0]
            transaction['Description'] += ' ' + cusip
            transaction['Symbol'] = cusip
            transaction['SecurityType'] = 'TREASURY BILL'
        transaction['Amount'] = self.__get_float(lines[-1])
        if last_string_index < -2:
            transaction['Quantity'] = self.__get_float(lines[last_string_index+1])
            if transaction['TransactionType'] in ['Bought', 'Sold', 'Redemption']:
                transaction['Quantity'] *= -math.copysign(1, transaction['Amount'])
        if last_string_index < -3:
            transaction['Price'] = self.__get_float(lines[last_string_index+2])
            if transaction['TransactionType'] in ['Redemption']:
                transaction['Price'] /= 100

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

    def __set_account_info(self):
        self.__set_name_pages()
        self.account_type = None
        self.account_number = None
        self.start_date = None
        self.end_date = None

        # get account info
        lines = self.statement.get_page_lines(self.__name_pages['Account Summary']['pages'][0])
        for line_idx in range(len(lines)):
            line = lines[line_idx]
            if self.account_type == None and 'Account' in line:
                self.account_type = line
                self.account_number = lines[line_idx+1]
            if 'For the Period' in line:
                period = line.split('For the Period ')[-1].strip()
                splits = period.split(',')
                year = splits[1].strip()
                splits = splits[0].split('-')
                
                self.start_date = splits[0].strip().split(' ')

                self.end_date = splits[1].strip().split(' ')
                if len(self.end_date) > 1:
                    self.end_date = '%s/%s/%s' % (self.end_date[0].strip(), self.end_date[1].strip(), year)
                else:
                    self.end_date = '%s/%s/%s' % (self.start_date[0].strip(), self.end_date[0].strip(), year)
                self.end_date = datetime.strptime(self.end_date, '%B/%d/%Y')

                self.start_date = '%s/%s/%s' % (self.start_date[0].strip(), self.start_date[1].strip(), year)
                self.start_date = datetime.strptime(self.start_date, '%B/%d/%Y')

