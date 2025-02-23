import glob
from .statement import *
from pprint import pp
import pandas as pd

class Portfolio():
    def __init__(self):
        # get statements
        # pdf_files = glob.glob('test_statements/*.pdf')
        # pdf_files = glob.glob('database/statements/*.pdf')
        pdf_files = glob.glob('database/statements_ms/*.pdf')
        
        # pdf_files = ['database/statements/Etrade_TRUST_2024_08.pdf']
        # pdf_files = ['database/statements/RO_2023_09_MS.pdf']
        # pdf_files = ['test_statements/156-109380_2012_07.pdf']

        # print('pdf files: %d' % len(pdf_files))

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
                    elif block[0].startswith('Envelope'):
                        company_statement = Fidelity(statement)
                    elif block[0] == 'Account carried by Citigroup Global Markets Inc.  Member SIPC.':
                        pass
                        # company_statement = Citi(statement)
                    elif block[0] == 'Schwab Retirement Plan Services, Inc.':
                        pass
                        # company_statement = Schwab(statement)
                    elif block[0] == 'SCOTTRADE, INC':
                        company_statement = Scottrade(statement)
                    elif block[0].startswith('Merrill Lynch Wealth Management'):
                        pass
                        # company_statement = Merrill_Lynch(statement)
                    if company_statement != None: break
                if company_statement != None: break
            if company_statement == None:
                if morgan_stanley:
                    company_statement = Morgan_Stanley_SB(statement)
                else:
                    pass
                    # print('\nUNKNOWNs: %s' % (pdf_file))
            else:
                company_statements.append(company_statement)
            
        # print('statements: %d' % len(company_statements))
        
        # holdings = set()
        # for company_statement in company_statements:
        #     for account_number, account_data in company_statement.accounts.items():
        #         holdings.update(account_data['holdings'].keys())
        #         # if 'JPMORGAN CHASE BK N A FID 46656MBD2' in account_data['holdings']:
        #         #     pp(account_data['holdings']['JPMORGAN CHASE BK N A FID 46656MBD2'])
        # pp(holdings)
