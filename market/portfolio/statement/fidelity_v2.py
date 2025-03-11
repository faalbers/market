from datetime import datetime
from pprint import pp
import math, copy
import pandas as pd

class Fidelity_V2():
    name = 'Fidelity_V2'

    def __init__(self, statement):
        self.statement = statement
        self.accounts = {}

        if self.statement.pdf_file != 'database/statements_fi\\UNIQUE_2014_3QTR.pdf': return

        # TODO text does not seem to be sequential AT ALL, will tackle this later
        return

        print('')
        print('%s: %s' % (self.name, self.statement.pdf_file))

        self.__set_name_pages()
        self.__set_accounts_info()
        self.__set_holdings()

        # pp(self.__name_pages['accounts'])
        # pp(self.accounts)

    def __set_holdings(self):
        for account_number, account_data in self.__name_pages['accounts'].items():
            # print('%s' % account_number)
            children = account_data['Account']['children']

            lines = children['Holdings']['lines']
            if len(lines) > 0:
                # print('\tHoldings')
                self.__add_holdings_other(lines, account_number, 'Holdings')

    def __add_holdings_other(self, lines, account_number, page_name):
        # add other holdings data to account holdings
        account = self.accounts[account_number]
        for line in lines:
            print('\t\t%s' % line)

    def __set_accounts_info(self):
        # HACK Not handling this anomaly
        if len(self.__name_pages['accounts']) == 0: return
        date_string = None
        for account_number, account_data in self.__name_pages['accounts'].items():
            self.accounts[account_number] = {'holdings': {}}
            page_num = account_data['Account']['pages'][0]
            for block in self.statement.get_page_blocks(page_num):
                if len(block) == 2 and block[1] == account_number:
                    self.accounts[account_number]['type'] = block[0].strip()
                if date_string == None and ' - ' in block[0] and block[0].count(' - ') == 1:
                    if block[0][-4:].isdigit():
                        date_string = block[0]
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
                    'Holdings': {
                        'stop': 'Transaction Details',
                        'lines': [],
                    },
                },
            },
        }

        for page_num, blocks in self.statement.get_blocks().items():
            for block in blocks:
                # print(page_num, block)
                if len(block) == 2:
                    account_number = block[1]
                    if account_number.replace('-', '').isdigit():
                        if account_number not in self.__name_pages['accounts']:
                            self.__name_pages['accounts'][account_number] = {}
                            self.__name_pages['accounts'][account_number]['Account'] = copy.deepcopy(self.__name_pages['Account'])
                        self.__name_pages['accounts'][account_number]['Account']['pages'].append(page_num)
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
                    if line.startswith(name_pages[current_name]['stop']):
                        name_pages[current_name]['lines'] = current_lines
                        current_name = None
                        current_lines = []
                        continue
            
            found_start = False
            # check if current lines block should start
            # go through start keywords and check if line starts with it
            for key in name_pages.keys():
                if line.startswith(key):
                    print(key)
                    current_name = key
                    found_start = True
                    break
            # since this line is a start key, skip it
            if found_start: continue

            if current_name != None:
                print(line)
                current_lines.append(line)
        
        for name, name_data in name_pages.items():
            if 'children' in name_data:
                self.__recurse_lines(name_data['children'], name_data['lines'])
