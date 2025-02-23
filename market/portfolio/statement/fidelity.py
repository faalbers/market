from datetime import datetime
from pprint import pp
import math
import pandas as pd

class Fidelity():
    name = 'Fidelity'

    def __init__(self, statement):
        self.statement = statement
        self.accounts = {}
        return

        print('')
        print('%s: %s' % (self.name, self.statement.pdf_file))

        # self.__test()

        self.__set_accounts_info()

        self.__handle_accounts()

        print('Start Date    : %s' % self.start_date)
        print('End Date      : %s' % self.end_date)
        for account in self.accounts:
            print('%s' % account['account_number'])
            print('%s' % account['account_name'])
            for transaction in account['transactions']:
                print()
                for param, value in transaction.items():
                    print('\t%s: %s' % (param, value))

    def __test(self):
        found = set()
        for line in self.statement.get_lines():
            if line.startswith('Total'):
                found.add(line)
        for line in found:
            print('\t%s' % line)


    def __set_accounts_info(self):
        self.accounts = []
        self.start_date = None
        self.end_date = None

        # get report blocks to check version and dates
        report_block = None
        for page_num in range(self.statement.page_count):
            page_blocks = self.statement.get_page_blocks(page_num)
            date_block = None
            for block_idx in range(len(page_blocks)):
                block = page_blocks[block_idx]
                if report_block == None and block[0] == 'INVESTMENT REPORT':
                    report_block = block
                    break
                if date_block == None and ' - ' in block[0]:
                    # NOTE: this is a hack
                    date_block = block
                if report_block == None and block[0] == 'Investment Report':
                    report_block = block + date_block
                    
            if report_block != None: break
        
        if report_block == None:
            raise Exception('Fidelity statement: not recognized')

        # get blocks for accounts info
        accounts_blocks = None
        account_block = None
        for page_num in range(self.statement.page_count):
            # check every page
            page_blocks = self.statement.get_page_blocks(page_num)
            for block in page_blocks:
                if accounts_blocks != None and block[0] == 'Ending Portfolio Value':
                    continue
                if accounts_blocks == None and block[0] == 'Portfolio Summary':
                    accounts_blocks = []
                    continue
                if accounts_blocks == None and account_block == None and block[0].startswith('Account #'):
                    account_block = block
                    continue
                
                if accounts_blocks != None: accounts_blocks.append(block)

            if accounts_blocks != None or account_block != None: break
        
        
        # get period
        dates = report_block[1].split('-')
        self.start_date = datetime.strptime(dates[0].strip(), '%B %d, %Y')
        self.end_date = datetime.strptime(dates[1].strip(), '%B %d, %Y')

        if report_block[0] == 'INVESTMENT REPORT':
            # handle new version
            if accounts_blocks != None:
                # handle multiple accounts
                # print('%s: NEW: MULTIPLE: %s' % (self.name, self.statement.pdf_file))
                accounts = None
                blocks = None
                for block in accounts_blocks:
                    if blocks != None and len(blocks) > 0 and block[0].replace('-', '').isdigit():
                        blocks.append(block)
                        accounts.append(blocks)
                        blocks = []
                        continue
                    if accounts == None and block[0] == 'Account':
                        accounts = []
                        blocks = []
                        continue
                    if blocks != None: blocks.append(block)
                last_account = None
                for account in accounts:
                    account_dict = {}
                    account_dict['account_number'] = account[-1][0]
                    account_dict['account_version'] = 'new'
                    account_dict['account_name'] = []
                    for block in account[:-1]: account_dict['account_name'] += block
                    account_dict['account_name'] = ' '.join(account_dict['account_name'])
                    account_dict['account_pages'] = int(account[-1][3])-1
                    if last_account != None:
                        last_account['account_pages'] = list(range(last_account['account_pages'], account_dict['account_pages']))
                    last_account = account_dict
                    self.accounts.append(account_dict)
                if last_account != None:
                    last_account['account_pages'] = list(range(last_account['account_pages'], self.statement.page_count))
            elif account_block != None:
                pass
                # handle one account
                # print('%s: NEW: SINGLE  : %s' % (self.name, self.statement.pdf_file))
                splits = account_block[0].split('#')
                account_dict = {}
                account_dict['account_number'] = splits[1].strip()
                account_dict['account_version'] = 'new'
                account_dict['account_name'] = account_block[1].strip()
                account_dict['account_pages'] = list(range(1,self.statement.page_count))
                self.accounts.append(account_dict)
        else:
            # not handling old version
            # print('%s: OLD: UNKNOWN : %s' % (self.name, self.statement.pdf_file))
            pass

    def __handle_accounts(self):
        if len(self.accounts) == 0: return

        # print('%s: %s' % (self.name, self.statement.pdf_file))
        # print('Start Date    : %s' % self.start_date)
        # print('End Date      : %s' % self.end_date)
        for account in self.accounts:
            # print(account['account_number'])
            # print(account['account_name'])
            name_pages = self.__set_name_pages(account['account_pages'])

            account['transactions'] = []
            for page_name, page_name_data in name_pages['Activity']['children'].items():
                if len(page_name_data['lines']) == 0: continue
                # print('\t%s' % page_name)
                # for line in page_name_data['lines']:
                #     print('\t\t%s' % line)
                account['transactions'] += self.__get_transactions(page_name_data['lines'], page_name)

    def __get_transactions(self, lines, page_name):
        transactions = []
        last_index = None
        current_transaction = {}
        for line_index in range(len(lines)):
            line = lines[line_index]
            line_digits = line.replace('/', '')
            if line_digits.isdigit() and line != line_digits and len(line_digits) <= 4:
                # create a datetime object from the date line
                date_elements = line.split('/')
                date = datetime(month=int(date_elements[0]), day=int(date_elements[1]), year=self.end_date.year)

                if 'TransactionDate' in current_transaction:
                    self.__parse_transaction(current_transaction, page_name)
                    transactions.append(current_transaction)
                
                current_transaction = {'TransactionDate': date, 'lines': []}

            elif 'TransactionDate' in current_transaction:
                current_transaction['lines'].append(line)
        
        # make sure the last transaction is added if needed
        if 'TransactionDate' in current_transaction:
            # trim lines if needed
            self.__parse_transaction(current_transaction, page_name)
            transactions.append(current_transaction)

        return transactions

    def __parse_transaction(self, transaction, page_name):
        self.__trim_transaction_lines(transaction, page_name)
        lines = transaction.pop('lines')

        if 'You Sold' in lines:
            transaction_type_idx = lines.index('You Sold')
            if page_name == 'Securities Bought & Sold':
                # for line in lines:
                #     print('\t\t\t%s' % line)
                transaction['TransactionType'] = 'Sold'
                transaction['Description'] = lines[0]
                transaction['Comments'] = ' '.join(lines[1:transaction_type_idx-1])
                transaction['Symbol'] = lines[transaction_type_idx-1]
                if self.__get_float(lines[-5]) != None:
                    transaction['Quantity'] = self.__get_float(lines[-5])
                    transaction['Price'] = self.__get_float(lines[-4])
                    transaction['Amount'] = self.__get_float(lines[-1])
                    if lines[-2] != '-': transaction['TransactionCost'] = self.__get_float(lines[-2])
                elif self.__get_float(lines[-4]) != None:
                    transaction['Quantity'] = self.__get_float(lines[-4])
                    transaction['Price'] = self.__get_float(lines[-3])
                    transaction['Amount'] = self.__get_float(lines[-1])
                    if lines[-2] != '-': transaction['TransactionCost'] = self.__get_float(lines[-2])
                else:
                    raise Exception('Fidelity statement: Sold action not recognized: %s' % page_name)
                # pp(transaction)
            elif page_name == 'Core Fund Activity':
                transaction['TransactionType'] = 'Sold'
                transaction['Description'] = lines[transaction_type_idx+1]
                transaction['Comments'] = ' '.join(lines[transaction_type_idx+2:-4])
                transaction['Quantity'] = self.__get_float(lines[-4])
                transaction['Price'] = self.__get_float(lines[-3])
                transaction['Amount'] = -self.__get_float(lines[-2])
                # pp(transaction)
            else:
                raise Exception('Fidelity statement: Sold action not recognized: %s' % page_name)
            
        elif 'You Bought' in lines:
            transaction_type_idx = lines.index('You Bought')
            if page_name == 'Securities Bought & Sold':
                transaction['TransactionType'] = 'Bought'
                transaction['Description'] = lines[0]
                transaction['Comments'] = ' '.join(lines[1:transaction_type_idx-1])
                transaction['Symbol'] = lines[transaction_type_idx-1]
                transaction['Quantity'] = self.__get_float(lines[-4])
                transaction['Price'] = self.__get_float(lines[-3])
                transaction['Amount'] = self.__get_float(lines[-1])
                if lines[-2] != '-': transaction['TransactionCost'] = self.__get_float(lines[-2])
                # pp(transaction)
            elif page_name == 'Core Fund Activity':
                transaction['TransactionType'] = 'Bought'
                transaction['Description'] = lines[transaction_type_idx+1]
                transaction['Comments'] = ' '.join(lines[transaction_type_idx+2:-4])
                transaction['Quantity'] = self.__get_float(lines[-4])
                transaction['Price'] = self.__get_float(lines[-3])
                transaction['Amount'] = -self.__get_float(lines[-2])
                # pp(transaction)
            else:
                raise Exception('Fidelity statement: Bought action not recognized: %s' % page_name)
                
        elif 'Interest Earned' in lines:
            transaction_type_idx = lines.index('Interest Earned')
            transaction['TransactionType'] = 'Interest'
            transaction['Description'] = lines[0]
            transaction['Symbol'] = lines[transaction_type_idx-1]
            transaction['Amount'] = self.__get_float(lines[-1])
            # pp(transaction)

        elif 'Reinvestment' in lines:
            transaction_type_idx = lines.index('Reinvestment')
            transaction['TransactionType'] = 'Reinvestment'
            if page_name == 'Dividends, Interest & Other Income':
                transaction['Description'] = lines[0]
                transaction['Comments'] = ' '.join(lines[1:transaction_type_idx-1])
                transaction['Symbol'] = lines[transaction_type_idx-1]
                transaction['Quantity'] = self.__get_float(lines[-3])
                transaction['Price'] = self.__get_float(lines[-2])
                transaction['Amount'] = self.__get_float(lines[-1])
                # pp(transaction)
            elif page_name == 'Core Fund Activity':
                transaction['Description'] = lines[transaction_type_idx+1]
                transaction['Comments'] = ' '.join(lines[transaction_type_idx+2:-4])
                transaction['Quantity'] = self.__get_float(lines[-4])
                transaction['Price'] = self.__get_float(lines[-3])
                transaction['Amount'] = -self.__get_float(lines[-2])
                # pp(transaction)
            else:
                raise Exception('Fidelity statement: Reinvestment action not recognized: %s' % page_name)

        elif 'Long-Term Cap Gain' in lines:
            transaction_type_idx = lines.index('Long-Term Cap Gain')
            transaction['TransactionType'] = 'LT Cap Gain Distribution'
            transaction['Description'] = lines[0]
            transaction['Symbol'] = lines[transaction_type_idx-1]
            transaction['Amount'] = self.__get_float(lines[-1])
            # pp(transaction)
        elif 'Short-Term Cap Gain' in lines:
            transaction_type_idx = lines.index('Short-Term Cap Gain')
            transaction['TransactionType'] = 'ST Cap Gain Distribution'
            transaction['Description'] = lines[0]
            transaction['Symbol'] = lines[transaction_type_idx-1]
            transaction['Amount'] = self.__get_float(lines[-1])
            # pp(transaction)
        elif 'Dividend Received' in lines:
            transaction_type_idx = lines.index('Dividend Received')
            transaction['TransactionType'] = 'Dividend'
            transaction['Description'] = ' '.join(lines[:transaction_type_idx-1])
            transaction['Symbol'] = lines[transaction_type_idx-1]
            transaction['Amount'] = self.__get_float(lines[-1])
            # pp(transaction)
        elif 'Transfer Of Assets' in lines:
            transaction_type_idx = lines.index('Transfer Of Assets')
            if page_name == 'Securities Transferred In':
                transaction['TransactionType'] = 'Transfer Of Assets'
                acat_split = ' '.join(lines[:transaction_type_idx-1]).split('ACAT')
                transaction['Description'] = acat_split[0].strip()
                transaction['Comments'] = acat_split[1].strip()
                transaction['Symbol'] = lines[transaction_type_idx-1]
                transaction['Quantity'] = self.__get_float(lines[-3])
                transaction['Price'] = self.__get_float(lines[-2])
                transaction['Amount'] = transaction['Quantity'] * transaction['Price']
                # pp(transaction)
        # elif 'Deposit Elan Cardsvc Redemption' in lines:
        #     transaction['TransactionType'] = 'Deposit Elan Cardsvc Redemption'
        # elif 'Transferred To' in lines:
        #     transaction['TransactionType'] = 'Transferred To'
        # elif 'Check Received Mobile Deposit' in lines:
        #     transaction['TransactionType'] = 'Check Received Mobile Deposit'
        # elif 'Check Received' in lines:
        #     transaction['TransactionType'] = 'Check Received'
        else:
            #leftovers
            pass
            # print('\tOther: %s' % page_name)
            # for line in lines:
            #     print('\t\t\t%s' % line)
    
    def __get_float(self, text):
        text = text.replace('$', '')
        text = text.replace(',', '')
        try:
            return float(text)
        except:
            return None

    def __trim_transaction_lines(self, transaction, page_name):
        continued_text = page_name + ' (continued)'
        if continued_text in transaction['lines']:
            investment_report_idx = transaction['lines'].index('INVESTMENT REPORT')
            transaction['lines'] = transaction['lines'][:investment_report_idx-3]

    def __set_name_pages(self, pages):
        name_pages = {
            'Holdings': {
                'stop': ['Total Holdings'],
                'lines': [],
                'children': {
                    'Core Account': {
                        'stop': ['Total Core Account'],
                        'lines': [],
                    },
                    'Mutual Funds': {
                        'stop': ['Total Mutual Funds'],
                        'lines': [],
                    },
                },
            },
            'Activity': {
                'stop': ['Estimated Cash Flow', 'Daily Additions and Subtractions'],
                'lines': [],
                'children': {
                    'Securities Bought & Sold': {
                        'stop': ['Total Securities Bought', 'Total Securities Sold'],
                        'lines': [],
                    },
                    'Securities Transferred In': {
                        'stop': ['Total Securities Transferred In'],
                        'lines': [],
                    },
                    'Dividends, Interest & Other Income': {
                        'stop': ['Total Dividends, Interest & Other Income'],
                        'lines': [],
                    },
                    'Core Fund Activity': {
                        'stop': ['Total Core Fund Activity'],
                        'lines': [],
                    },
                    'Contributions': {
                        'stop': ['Total Contributions'],
                        'lines': [],
                    },
                    'Deposits': {
                        'stop': ['Total Deposits'],
                        'lines': [],
                    },
                    'Exchanges Out': {
                        'stop': ['Total Exchanges Out'],
                        'lines': [],
                    },
                },
            },
        }
        lines = []
        for page_num in pages:
            blocks = self.statement.get_page_blocks(page_num)
            for block in blocks:
                lines += block
        self.__recurse_lines(name_pages, lines)
        return name_pages

    def __recurse_lines(self, name_pages, lines):
        current_name = None
        for line in lines:
            
            if current_name != None:
                if name_pages[current_name]['stop'] != None:
                    for stop_line in name_pages[current_name]['stop']:
                        if line.startswith(stop_line):
                            current_name = None
                            break
                    if current_name == None: continue
            
            if line in name_pages.keys():
                current_name = line
                continue

            if current_name != None:
                name_pages[current_name]['lines'].append(line)

        for name, name_data in name_pages.items():
            if 'children' in name_data:
                self.__recurse_lines(name_data['children'], name_data['lines'])
