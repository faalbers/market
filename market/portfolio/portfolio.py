import glob
from .statement import *
from pprint import pp
import pandas as pd

class Portfolio():
    def __init__(self):
        # get statements
        pdf_files = []
        # pdf_files = glob.glob('test_statements/*.pdf')
        # pdf_files = glob.glob('database/statements/*.pdf')
        
        pdf_files += glob.glob('database/statements_ms/*.pdf')
        # pdf_files += glob.glob('database/statements_fi/*.pdf')
        # pdf_files += glob.glob('database/statements_st/*.pdf')
        # pdf_files += glob.glob('database/statements_ml/*.pdf')
        
        # pdf_files = ['database/statements/Etrade_TRUST_2024_08.pdf']
        # pdf_files = ['database/statements/RO_2023_09_MS.pdf']
        # pdf_files = ['test_statements/156-109380_2012_07.pdf']

        # print('pdf files: %d' % len(pdf_files))
        citi = [
            'Citigroup Global Markets',
            'Account carried by Citigroup Global Markets',
        ]
        company_statements = []
        for pdf_file in pdf_files:
            statement = Statement(pdf_file)
            company_statement = None

            morgan_stanley = False
            for page_num, blocks in statement.get_blocks().items():
                for block in blocks:
                    if 'Morgan Stanley' in block[0]:
                        morgan_stanley = True
                    elif morgan_stanley and block[0] == 'Account Summary':
                        company_statement = Morgan_Stanley(statement)
                    elif block[0] in ['Account At A Glance', 'Portfolio At A Glance']:
                        company_statement = Etrade(statement)
                    elif block[0].startswith('INVESTMENT REPORT'):
                        company_statement = Fidelity(statement)
                    elif block[0].startswith('Investment Report'):
                        company_statement = Fidelity_V2(statement)
                    elif 'Citigroup' in block[0]:
                        company_statement = Citi(statement)
                    elif block[0].startswith('Schwab'):
                        if block[0].startswith('Schwab Retirement Plan Services'):
                            pass # Not doing Schwab, no good info
                            # company_statement = Schwab(statement)
                        else:
                            pass # Not doing Schwab, no good info
                            # company_statement = Schwab_V2(statement)
                    elif block[0] == 'SCOTTRADE, INC':
                        company_statement = Scottrade(statement)
                    elif block[0].startswith('Merrill Lynch'):
                        company_statement = Merrill_Lynch(statement)
                    if company_statement != None: break
                if company_statement != None: break
            if company_statement == None:
                if morgan_stanley:
                    pass
                    # company_statement = Morgan_Stanley_SB(statement)
                else:
                    pass
                    # print('\nUNKNOWNs: %s' % (pdf_file))
            else:
                company_statements.append(company_statement)
            
        # print('statements: %d' % len(company_statements))

        # accounts = {}
        # holdings = {}
        # for company_statement in company_statements:
        #     if not company_statement.name in accounts:
        #         accounts[company_statement.name] = set()
        #     for account_number, account_data in company_statement.accounts.items():
        #         accounts[company_statement.name].add(account_number)
        #         for security, security_data in account_data['holdings'].items():
        #             if not security_data['type'] in holdings:
        #                 holdings[security_data['type']] = {}
        #             if not security in holdings[security_data['type']]:
        #                 holdings[security_data['type']][security] = set()
        #             holdings[security_data['type']][security].add(security_data['symbol'])
        #             holdings[security_data['type']][security].add(security_data['cusip'])

        # pp(accounts)
        # pp(holdings)
