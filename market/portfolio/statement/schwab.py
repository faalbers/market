from datetime import datetime
from pprint import pp
import math
import pandas as pd

class Schwab():
    name = 'Schwab'

    def __init__(self, statement):
        self.statement = statement
        print('')
        print('%s: %s' % (self.name, self.statement.pdf_file))
        return
