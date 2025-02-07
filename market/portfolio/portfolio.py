import glob
from .statement import *
from pprint import pp
import pandas as pd

class Portfolio():
    def __init__(self):
        # get statements
        # pdf_files = glob.glob('test_statements/*.pdf')
        pdf_files = glob.glob('database/statements/*.pdf')
        
        # pdf_files = ['database/statements/Etrade_TRUST_2024_08.pdf']
        # pdf_files = ['database/statements/RO_2023_09_MS.pdf']

        # print('pdf files: %d' % len(pdf_files))

        company_statements = []
        for pdf_file in pdf_files:
            statement = Statement(pdf_file)
            blocks = statement.get_page_blocks(0)
            statement_type = None
            company_statement = None
            block_starts = []
            company_statements_count = len(company_statements)
            for block in blocks:
                block_starts.append(block[0])
                if block[0].startswith('Envelope'):
                    statement_type = 'Fidelity'
                    break
                elif block[0] in ['Account At A Glance', 'Portfolio At A Glance']:
                # elif block[0] in ['Account At A Glance']:
                    statement_type = 'Etrade'
                    # company_statement = Etrade(statement)
                    # company_statements.append(company_statement)
                    break
                elif block[0] == 'Morgan Stanley Smith Barney LLC. Member SIPC.':
                    statement_type = 'Morgan Stanley'
                    company_statement = Morgan_Stanley(statement)
                    company_statements.append(company_statement)
                    break
                elif block[0] == 'Morgan Stanley Private Wealth Management, a division of Morgan Stanley Smith Barney LLC.':
                    statement_type = 'Morgan Stanley Private Wealth Management'
                    # company_statement = Morgan_Stanley_Private(statement)
                    # company_statements.append(company_statement)
                    break
                elif block[0] == 'Schwab Retirement Plan Services, Inc.':
                    statement_type = 'Schwab'
                    break
                elif block[0] == 'SCOTTRADE, INC':
                    statement_type = 'ScottTrade'
                    break
                elif block[0].startswith('Merrill Lynch Wealth Management'):
                    statement_type = 'Merrill Lynch'
                    break
            # if company_statements_count == len(company_statements):
            #     print(pdf_file)
            # if (len(company_statements) - company_statements_count) > 1:
            #     print(pdf_file)
            #     for statement in company_statements:
            #         print('\t%s: %s' % (statement.name, statement.statement.pdf_file))
            # if statement_type != None:
            #     print(statement_type)
            # else:
            #     for text in block_starts:
            #         print('\t%s' % text)
        # print('statements: %d' % len(company_statements))
