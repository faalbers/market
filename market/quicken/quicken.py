from pprint import pp
from datetime import datetime
import pandas as pd
import numpy as np
from ..portfolio_old import Portfolio

class QIF():
    def __init__(self, qif_file):
        # parse all lines i qif file
        line = '*'
        self.qif_data = []
        section = {}
        entry = {}
        with open(qif_file, 'r') as f:
            while line:
                if line.startswith('!'):
                    # start a section
                    if len(section) > 0:
                        self.qif_data.append(section)
                    # start a new section
                    section = {'header': line.strip('\n')[1:].strip(), 'entries': []}
                    # start a new empty entry
                    entry = {}
                elif line == '^\n':
                    # if entry is not empty, add entry to section entries
                    if len(entry) > 0:
                        section['entries'].append(entry)
                    # create new empty entry
                    entry = {}
                elif line != '*':
                    # add entry to section entries
                    cleanLine = line.strip('\n').strip()
                    key = cleanLine[0]
                    value = cleanLine[1:]
                    # add key in entry 
                    if not key in entry:
                        entry[key] = []
                    entry[key].append(value)

                line = f.readline()
        
        if False:
            # write out for visualization
            with open('qifSections.txt', 'w') as f:
                pp(self.qif_data, f)

        # parse qif data
        headers = {}
        autoSwitchCount = 0
        self.accounts = []
        self.securities = []
        account = {}
        for section in self.qif_data:
            # keep track of headers
            if not section['header'] in headers:
                headers[section['header']] = 0
            headers[section['header']] += 1

            # set autoswitch count, not sure yet what it's needed for
            if section['header'] == 'Option:AutoSwitch':
                autoSwitchCount += 1

            # get security section
            elif section['header'] == 'Type:Security':
                entry = section['entries'][0]
                security = {}
                security['name'] = entry['N'][0]
                security['symbol'] = None
                if 'S' in entry:
                    security['symbol'] = entry['S'][0]
                security['type'] = entry['T'][0]
                self.securities.append(security)

            # get account section
            elif section['header'] == 'Account':
                # if autoSwitchCount == 1:
                #     pass
                # if autoSwitchCount == 2:
                entry = section['entries'][0]
                account['name'] = entry['N'][0]
                account['type'] = entry['T'][0]
                if 'D' in entry:
                    account['description'] = entry['D'][0]
            elif section['header'] == 'Type:Bank':
                accType = 'Bank'
                if account['type'] == accType:
                    self.accounts.append(account)
                    account = {}
            elif section['header'] == 'Type:CCard':
                accType = 'CCard'
                if account['type'] == accType:
                    self.accounts.append(account)
                    account = {}
            elif section['header'] == 'Type:Cash':
                accType = 'Cash'
                if account['type'] == accType:
                    self.accounts.append(account)
                    account = {}
            elif section['header'] == 'Type:Oth A':
                accType = 'Oth A'
                if account['type'] == accType:
                    self.accounts.append(account)
                    account = {}
            elif section['header'] == 'Type:Oth L':
                accType = 'Oth L'
                if account['type'] == accType:
                    self.accounts.append(account)
                    account = {}
            elif section['header'] == 'Type:Invst':
                accType = 'Invst'
                if account['type'] == accType:
                    account['transactions'] = QIF.__account_transactions(section['entries'], accType)
                    self.accounts.append(account)
                    account = {}

    def __account_transactions(entries, accType):
        transactions = []
        for entry in entries:
            dataTypes = set(entry.keys())
            # not handling these for now
            dataTypes -= {'$', 'T', 'C'}
            transaction = {}
            
            # get date
            date = entry['D'][0].split('/')
            month = int(date[0].strip())
            date = date[1].split("'")
            day = int(date[0].strip())
            year = int(date[1].strip())+2000
            transaction['date'] = datetime(day=day, month=month, year=year)
            dataTypes.remove('D')
            
            # get values
            if 'U' in entry:
                transaction['amount'] = float(entry['U'][0].replace(',',''))
                dataTypes.remove('U')
            if 'N' in entry:
                if accType == 'Invst':
                    transaction['action'] = entry['N'][0]
                dataTypes.remove('N')
            if 'P' in entry:
                if accType == 'Invst':
                    transaction['description'] = entry['P'][0]
                dataTypes.remove('P')
            if 'L' in entry:
                if accType == 'Invst':
                    transaction['transferAccount'] = entry['L'][0]
                dataTypes.remove('L')
            if 'M' in entry:
                if accType == 'Invst':
                    transaction['memo'] = entry['M'][0]
                dataTypes.remove('M')
            if 'Y' in entry:
                if accType == 'Invst':
                    transaction['security'] = entry['Y'][0]
                dataTypes.remove('Y')
            if 'I' in entry:
                if accType == 'Invst':
                    transaction['price'] = float(entry['I'][0].replace(',',''))
                dataTypes.remove('I')
            if 'Q' in entry:
                if accType == 'Invst':
                    transaction['shares'] = float(entry['Q'][0].replace(',',''))
                dataTypes.remove('Q')
            if 'O' in entry:
                if accType == 'Invst':
                    transaction['commission'] = float(entry['O'][0].replace(',',''))
                dataTypes.remove('O')
            
            # check if we missed any data
            if len(dataTypes) > 0:
                pp(transaction)
                pp(entry)
                raise ValueError('unhandled data types: ' + str(dataTypes))
            
            transactions.append(transaction)
        
        return transactions

class Quicken():
    def __init__(self, qif_file):
        self.qif = QIF(qif_file)

    def get_investment_accounts(self):
        accounts = []
        for account in self.qif.accounts:
            if account['type'] != 'Invst': continue
            inv_account = {'name': account['name']}
            inv_account['transactions'] = pd.DataFrame(account['transactions'])
            accounts.append(inv_account)

        return accounts
    
    def get_securities(self):
        securities = pd.DataFrame(self.qif.securities)
        return securities

    def get_portfolios(self):
        # group by shares functionality
        shares_in = ['Buy', 'ShrsIn', 'ReinvDiv', 'ReinvLg', 'ReinvSh']
        shares_out = ['Sell', 'ShrsOut']
        shares_split = ['StkSplit']
        
        # find security symbols
        securities = self.get_securities()
        securities.drop_duplicates(subset='name', keep='first', inplace=True)
        securities.set_index('name', verify_integrity=True, inplace=True)

        # create portfolios
        portfolios = []
        for account in self.get_investment_accounts():
            # print(account['transactions']['action'].unique())

            # get sharesin transactions
            df_transactions_in = account['transactions'][account['transactions']['action'].isin(shares_in)]
            df_transactions_in = df_transactions_in.dropna(subset='shares')
            df_transactions_in = df_transactions_in[['date', 'action', 'shares', 'amount', 'security']]
            df_transactions_in['symbol'] = df_transactions_in['security'].map(securities['symbol'])
            df_transactions_in['price'] = df_transactions_in['amount'] / df_transactions_in['shares']

            # get shares out transactions
            df_transactions_out = account['transactions'][account['transactions']['action'].isin(shares_out)]
            df_transactions_out = df_transactions_out.dropna(subset='shares')
            df_transactions_out = df_transactions_out[['date', 'action', 'shares', 'amount', 'security']]
            df_transactions_out['symbol'] = df_transactions_out['security'].map(securities['symbol'])
            df_transactions_out['price'] = df_transactions_out['amount'] / df_transactions_out['shares']
            df_transactions_out['shares'] = -df_transactions_out['shares']
            df_transactions_out['amount'] = -df_transactions_out['amount']

            # get split transactions
            df_transactions_split = account['transactions'][account['transactions']['action'].isin(shares_split)]
            df_transactions_split = df_transactions_split.dropna(subset='shares')
            df_transactions_split = df_transactions_split[['date', 'action', 'shares', 'amount', 'security']]
            df_transactions_split['symbol'] = df_transactions_split['security'].map(securities['symbol'])
            df_transactions_split['price'] = np.nan
            df_transactions_split['shares'] = df_transactions_split['shares'] / 10

            # get dividend payouts
            df_transactions_div = account['transactions'][account['transactions']['action'] == 'Div']
            df_transactions_div = df_transactions_div[['date', 'action', 'shares', 'amount', 'security']]
            df_transactions_div['symbol'] = df_transactions_div['security'].map(securities['symbol'])
            df_transactions_div['price'] = np.nan

            # combine them and reset index
            df_transactions = pd.concat(
                [df_transactions_in, df_transactions_out, df_transactions_split, df_transactions_div])
            df_transactions = df_transactions.sort_values(by='date')
            df_transactions = df_transactions.set_index('date')

            # create portfolios
            portfolio = Portfolio(account['name'], df_transactions)
            portfolios.append(portfolio)

        return portfolios
