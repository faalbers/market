from datetime import datetime
from pprint import pp
import math
import pandas as pd

class Morgan_Stanley_SB():
    name = 'Morgan_Stanley_SB'

    def __init__(self, statement):
        self.statement = statement
        self.accounts = {}

        # if self.statement.pdf_file != 'database/statements_ms\\Trust_2024_05_31.pdf': return

        # return
        
        print('')
        print('%s: %s' % (self.name, self.statement.pdf_file))

