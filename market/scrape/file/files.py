from .file import File
import logging
from ...database import Database
import glob, os
from pathlib import Path
import pandas as pd

class File_Files(File):
    dbName = 'file_files'

    @staticmethod
    def get_table_names(table_name):
        # if table_name == 'all':
        #     return list(const.QUOTESUMMARY_MODULES.keys())
        return [table_name]

    def __init__(self, key_values=[], table_names=[]):
        self.logger = logging.getLogger('vault_multi')
        super().__init__()
        self.db = Database(self.dbName)

        self.logger.info('File:    Files update')

        self.readCSV()

        self.logger.info('File:    Files update done')

    def readCSV(self):
        csv_files = glob.glob(self.dataPath+'*.csv')

        db_connection = self.db.get_connection()
        for csv_file in csv_files:
            file_date = int(os.path.getmtime(csv_file))
            data_name = Path(csv_file).stem

            # read file into database
            data = pd.read_csv(csv_file)
            data.to_sql(data_name, con=db_connection, index=False, if_exists='replace')

            self.logger.info('File:    Added CSV file: %s' % data_name)
