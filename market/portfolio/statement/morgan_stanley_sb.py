from datetime import datetime
from pprint import pp
import math
import pandas as pd

class Morgan_Stanley_SB():
    name = 'Morgan_Stanley_SB'

    def __init__(self, statement):
        self.statement = statement
        print('')
        print('%s: %s' % (self.name, self.statement.pdf_file))
        return
