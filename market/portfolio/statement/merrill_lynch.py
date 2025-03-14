from datetime import datetime
from pprint import pp
import math, copy
import pandas as pd

class Merrill_Lynch():
    name = 'Merrill_Lynch'

    def __init__(self, statement):
        self.statement = statement
        self.accounts = {}

        # if self.statement.pdf_file != 'database/statements_ml\\7WA 15527-2013-10-12.pdf': return

        return

        print('')
        print('%s: %s' % (self.name, self.statement.pdf_file))

        self.__set_name_pages()
        self.__set_accounts_info()
        self.__set_holdings()

        # pp(self.__name_pages['accounts'])
        pp(self.accounts)

    def __set_holdings(self):
        for account_number, account_data in self.__name_pages['accounts'].items():
            # print('%s' % account_number)
            children = account_data['Account']['children']

            lines = children['EQUITIES']['lines']
            if len(lines) > 0:
                print('\tEQUITIES')
                self.__add_stock(lines, account_number)

    def __add_stock(self, lines, account_number):
        # add core data to account holdings
        account = self.accounts[account_number]

        # not even parsing since it's always only one
        lines = lines[lines.index('Yield%')+1:]
        security = lines[0].strip()
        symbol = lines[1].strip()
        quantity = self.__get_float(lines[3].strip())
        account['holdings'][security] = {
            'type': 'stock', 'symbol': symbol, 'cusip': None, 'date': account['end_date'], 'quantity': quantity, 'transactions': []}

    def __get_float(self, text):
        text = text.replace('$', '')
        text = text.replace(',', '')
        try:
            return float(text)
        except:
            return None

    def __set_accounts_info(self):
        date_string = None
        for account_number, account_data in self.__name_pages['accounts'].items():
            self.accounts[account_number] = {'type': 'INDIVIDUAL INVESTOR ACCOUNT', 'statement': self.statement.pdf_file, 'holdings': {}}
            if date_string == None:
                page_num = account_data['Account']['pages'][0]
                for block in self.statement.get_page_blocks(page_num):
                    if block[0].startswith('INDIVIDUAL INVESTOR ACCOUNT') and ' - ' in block[1]:
                        date_string = block[1].strip()
                        break
                    if ' - ' in block[0]:
                        date_string = block[0].strip()
                        break
                    if len(block) > 1 and block[1].startswith('- '):
                        date_string = ' '.join(block[:2]).strip()
                        break
        dates = date_string.split(' - ')
        start_date = datetime.strptime(dates[0].strip(), '%B %d, %Y')
        end_date = datetime.strptime(dates[1].strip(), '%B %d, %Y')
        for account_number, account_data in self.accounts.items():
            account_data['start_date'] = start_date
            account_data['end_date'] = end_date

    def __set_name_pages(self):
        # search structure:
        # key words under children are the start key words of blocks of lines
        # the 'stop' keyword is the end key word of blocks of those lines
        # the 'lines' feyword has all the lines of that block
        self.__name_pages = {
            'accounts': {},
            'Account': {
                'pages': [],
                'children': {
                    'EQUITIES': {
                        'stop': 'TOTAL',
                        'lines': [],
                    },
                },
            },
        }

        for page_num, blocks in self.statement.get_blocks().items():
            for block_idx in range(len(blocks)):
                block = blocks[block_idx]
                if block[0].startswith('Account'):
                    account_number = block[0]
                    if len(account_number) <= 15:
                        account_number = ' '.join(block[0:2])
                    account_number = account_number.split(':')[1].strip()
                    if account_number not in self.__name_pages['accounts']:
                        self.__name_pages['accounts'][account_number] = {}
                        self.__name_pages['accounts'][account_number]['Account'] = copy.deepcopy(self.__name_pages['Account'])
                    self.__name_pages['accounts'][account_number]['Account']['pages'].append(page_num)
                    break

        for account_number, account_data in self.__name_pages['accounts'].items():
            for pages_name, page_data in account_data.items():
                if len(page_data['pages']) > 0:
                    if len(page_data['children']) > 0:
                        print(page_data['pages'])
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
        for line in lines:
            if current_name != None:
                if 'stop' in name_pages[current_name]:
                    if line == name_pages[current_name]['stop']:
                        print('stop: %s - with: %s' % (current_name, line))
                        name_pages[current_name]['lines'] = current_lines
                        current_name = None
                        current_lines = []
                        continue
            
            if line in name_pages:
                print('start: new: %s - old: %s' % (line, current_name))
                current_name = line
                current_lines = []
                continue

            if current_name != None:
                current_lines.append(line)
        
        if current_name != None:
            pass
            # raise Exception('last current name not stopped: %s' % current_name)
            # print('%s: %s' % (self.name, self.statement.pdf_file))
            # print(current_name)
            # for line in current_lines:
            #     print('\t%s' % line)

        for name, name_data in name_pages.items():
            if 'children' in name_data:
                self.__recurse_lines(name_data['children'], name_data['lines'])
