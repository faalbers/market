from datetime import datetime
from pprint import pp
import math, copy
import pandas as pd

class Fidelity():
    name = 'Fidelity'

    def __init__(self, statement):
        self.statement = statement
        self.accounts = {}

        # if self.statement.pdf_file != 'database/statements_fi\\UNIQUE_2018_08.pdf': return

        return

        # print('')
        # print('%s: %s' % (self.name, self.statement.pdf_file))

        self.__set_name_pages()
        self.__set_accounts_info()
        self.__set_holdings()

        # pp(self.__name_pages['accounts'])
        # pp(self.accounts)

    def __set_holdings(self):
        for account_number, account_data in self.__name_pages['accounts'].items():
            # print('%s' % account_number)
            children = account_data['Account #']['children']

            lines = children['Holdings']['lines']
            if len(lines) > 0:
                # print('\tHoldings')
                self.__add_holdings_other(lines, account_number, 'Holdings')

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

    def __add_holdings_other(self, lines, account_number, page_name):
        # add other holdings data to account holdings
        account = self.accounts[account_number]
        lines = self.__trim_lines(lines, page_name)

        for line_idx in range(len(lines)):
            line = lines[line_idx]
            if line.isupper() and '(' in line and ')' in line:
                security = line.strip()
                values = lines[line_idx+1:]
                quantity = self.__get_float(values[2])
                price = self.__get_float(values[3])
                account['holdings'][security] = {
                    'type': 'college fund', 'symbol': None, 'cusip': None, 'quantity': quantity, 'price': price, 'date': account['end_date'],
                    'transactions': []}

    def __add_core(self, lines, account_number, page_name):
        # add core data to account holdings
        account = self.accounts[account_number]
        if 'EY (%)' in lines:
            start_string = 'EY (%)'
        elif '(EY)' in lines:
            start_string = '(EY)'
        lines = self.__trim_lines(lines, page_name, start_string)

        for line_idx in range(len(lines)):
            line = lines[line_idx]
            if line.isupper() and '(' in line and ')' in line:
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
                    'type': 't bill', 'symbol': None, 'cusip': cusip, 'face_value': face_value, 'date': account['end_date'], 'total_cost': total_cost,
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
            self.accounts[account_number] = {'holdings': {}}
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
                    'Holdings': {
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
                        # print('stop: %s with: %s' % (current_name, line))
                        name_pages[current_name]['lines'] = current_lines
                        current_name = None
                        current_lines = []
                        continue
            
            if line in name_pages:
                # HACK
                if current_name != None and line in ['Holdings']: continue
                # print('start: new: %s old: %s' % (line, current_name))
                current_name = line
                current_lines = []
                continue

            if current_name != None:
                current_lines.append(line)
        
        # if 'Holding' is still open that's OK. others raise an exception
        if current_name != None:
            if not current_name in ['Holdings']:
                raise Exception('last current name not stopped: %s' % current_name)
                # print('%s: %s' % (self.name, self.statement.pdf_file))
                # print(current_name)
                # for line in current_lines:
                #     print('\t%s' % line)

        for name, name_data in name_pages.items():
            if 'children' in name_data:
                self.__recurse_lines(name_data['children'], name_data['lines'])
