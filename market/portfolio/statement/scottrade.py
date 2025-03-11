from datetime import datetime
from pprint import pp
import math, copy
import pandas as pd

class Scottrade():
    name = 'Scottrade'

    def __init__(self, statement):
        self.statement = statement
        self.accounts = {}

        # if self.statement.pdf_file != 'database/statements_st\\STRO_2014-06.pdf': return

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

            lines = children['SECURITY POSITIONS']['lines']
            if len(lines) > 0:
                # print('\tSECURITY POSITIONS')
                self.__add_stock(lines, account_number)

    def __add_stock(self, lines, account_number):
        # add core data to account holdings
        account = self.accounts[account_number]

        # lines = lines[lines.index('Cur. Yld')+1:]
        lines = self.__trim_lines(lines, account_number, 'Cur. Yld')

        for line_idx in range(len(lines)):
            line = lines[line_idx]
            if line in ['CASH', 'MARGIN']:
                symbol = lines[line_idx+1]
                if symbol.endswith('XX'):
                    security_type = 'money market fund'
                elif symbol.endswith('X'):
                    security_type = 'mutual fund'
                else:
                    security_type = 'stock'
                quantity = self.__get_float(lines[line_idx+2])
                security = lines[line_idx+3]
                account['holdings'][security] = {
                    'type': security_type, 'symbol': symbol, 'cusip': None, 'date': account['end_date'], 'quantity': quantity, 'transactions': []}

    def __get_float(self, text):
        text = text.replace('$', '')
        text = text.replace(',', '')
        try:
            return float(text)
        except:
            return None

    def __trim_lines(self, lines, account_number, start_string=None):
        trim_blocks = []
        trim_block = []
        for line in lines:
            if line.startswith('Page '):
                trim_blocks.append(trim_block)
                trim_block = []
                continue
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

    def __set_accounts_info(self):
        for account_number, account_data in self.__name_pages['accounts'].items():
            self.accounts[account_number] = {'holdings': {}}
            page_num = account_data['Account']['pages'][0]
            blocks = self.statement.get_page_blocks(page_num)
            for block_idx in range(len(blocks)):
                block = blocks[block_idx]
                if block[0] == 'Period Beginning':
                    self.accounts[account_number]['start_date'] = datetime.strptime(blocks[block_idx+1][0].strip(), '%m / %d / %Y')
                    self.accounts[account_number]['end_date'] = datetime.strptime(blocks[block_idx+1][1].strip(), '%m / %d / %Y')
                    self.accounts[account_number]['type'] = None
                    break

    def __set_name_pages(self):
        keywords = [
            'BANK DEPOSIT ACTIVITY',
            'CASH ACCOUNT ACTIVITY',
            'MARGIN ACCOUNT ACTIVITY',
            'SECURITY POSITIONS',
            'TRADES PENDING SETTLEMENT',
        ]
        self.__name_pages = {
            'accounts': {},
            'Account': {
                'pages': [],
                'children': {
                    'SECURITY POSITIONS': {
                        'stop': 'TOTAL',
                        'lines': [],
                    },
                },
            },
        }

        # search first page for 'Account Number'
        blocks = self.statement.get_page_blocks(0)
        for block_idx in range(len(blocks)):
            block = blocks[block_idx]
            if block[0] == 'Account Number':
                account_number = blocks[block_idx+1][0]
                self.__name_pages['accounts'][account_number] = {}
                self.__name_pages['accounts'][account_number]['Account'] = copy.deepcopy(self.__name_pages['Account'])
                self.__name_pages['accounts'][account_number]['Account']['pages'] = list(range(self.statement.page_count))
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
                    if line == name_pages[current_name]['stop']:
                        # print('stop: %s - with: %s' % (current_name, line))
                        name_pages[current_name]['lines'] = current_lines
                        current_name = None
                        current_lines = []
                        continue
            
            if line in name_pages:
                # print('start: new: %s - old: %s' % (line, current_name))
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
