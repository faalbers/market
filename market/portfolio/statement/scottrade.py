from datetime import datetime
from pprint import pp
import math
import pandas as pd

class Scottrade():
    name = 'Scottrade'

    def __init__(self, statement):
        self.statement = statement
        self.accounts = {}
        return

        print('')
        print('%s: %s' % (self.name, self.statement.pdf_file))

        # if len(block[0]) == 8 and block[0].count('/') == 2:
        #     print('\t%s' % block)

        self.__set_account_info()
        self.__set_transactions()

        # print('Account Number: %s' % self.account_number)
        # print('Account Type  : %s' % self.account_type)
        # print('Start Date    : %s' % self.start_date)
        # print('End Date      : %s' % self.end_date)


    def __set_account_info(self):
        self.__set_name_pages()
        self.account_number = self.name_pages['Account Number']['lines'][1]
        self.account_type = 'BROKER ACCOUNT'
        self.start_date = self.name_pages['Account Number']['lines'][5]
        self.start_date = datetime.strptime(self.start_date, '%m / %d / %Y')
        self.end_date = self.name_pages['Account Number']['lines'][6]
        self.end_date = datetime.strptime(self.end_date, '%m / %d / %Y')

    def __set_transactions(self):
        self.transactions = []

        # TODO: Maybe pop lines after using them ?
        self.__get_transactions(self.name_pages['CASH ACCOUNT ACTIVITY']['lines'])
        # self.__get_transactions(self.name_pages['MARGIN ACCOUNT ACTIVITY']['lines'])

    def __get_transactions(self, lines):
        current_transaction = {}
        for line in lines:
            if len(line) == 8 and line.count('/') == 2:
                if 'TransactionDate' in current_transaction:
                    self.__parse_transaction(current_transaction)
                    self.transactions.append(current_transaction)
                date = datetime.strptime(line, '%m/%d/%y')
                current_transaction = {'TransactionDate': date, 'lines': []}
                continue
            elif 'TransactionDate' in current_transaction:
                current_transaction['lines'].append(line)
        
        # make sure the last transaction is added if needed
        if 'TransactionDate' in current_transaction:
            # trim lines if needed
            self.__parse_transaction(current_transaction)
            self.transactions.append(current_transaction)

    def __parse_transaction(self, transaction):
        self.__trim_transaction_lines(transaction)
        lines = transaction.pop('lines')
        transaction_types = [
            'DIV REINVESTMENT',
            'LONG TERM CAP GAIN',
            'LONG TERM CAP',
            'ST CAPITAL GAIN',
            'TAXABLE DIVIDEND',
            'ACCOUNT TRANSFER',
            'IRA INTRL TRNSFR IN',
            'IRA INTRL TRNSFR OUT',
            'INTEREST EARNED',
            'STATEMENT FEE',
            'ADJUSTMENT',
            'RECEIVE SECURITIES',
            'BOUGHT',
            'SOLD',
            'REVERSE SPLIT',
            'CASH IN LIEU',
            'NAME CHANGE',
            'CORPORATE ACTION',
            'DELIVER SECURITIES',
            'RECEIVE',
            'CREDIT INTEREST',
            ]
        # if not lines[0] in transaction_types:
        #     print('%s: %s' % (self.name, self.statement.pdf_file))
        #     pp(lines)
        if lines[0] in ['BOUGHT', 'SOLD']:
            print('%s: %s' % (self.name, self.statement.pdf_file))
            pp(lines)

    def __trim_transaction_lines(self, transaction):
        #     transaction['lines'] = transaction['lines'][:investment_report_idx-3]
        if self.account_number in transaction['lines'] and 'OPENING BALANCE' in transaction['lines']:
            transaction['lines'] = transaction['lines'][:transaction['lines'].index(self.account_number)]
            return
        for line_idx in range(len(transaction['lines'])):
            if  transaction['lines'][line_idx].startswith('Page:'):
                transaction['lines'] = transaction['lines'][:line_idx]
                return

    def __set_name_pages(self):
        self.name_pages = {
            'Account Number': {
                'stop': ['INFORMATION UPDATE'],
                'lines': [],
            },
            'CASH ACCOUNT ACTIVITY': {
                'stop': ['CLOSING BALANCE'],
                'lines': [],
            },
            'MARGIN ACCOUNT ACTIVITY': {
                'stop': ['CLOSING BALANCE'],
                'lines': [],
            },
        }
        lines = self.statement.get_lines()
        self.__recurse_lines(self.name_pages, lines)

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
