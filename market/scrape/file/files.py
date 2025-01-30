from .file import File
import logging
from ...database import Database
import glob, os
from pathlib import Path
import pandas as pd
from pprint import pp

class File_Files(File):
    dbName = 'file_files'

    @staticmethod
    def get_table_names(table_name):
        if table_name == 'all':
            db = Database(File_Files.dbName)
            return sorted(db.table_read('status_db', column_values=['table_name']).keys())
        return [table_name]

    def __init__(self, key_values=[], table_names=[]):
        self.logger = logging.getLogger('vault_multi')
        super().__init__()
        self.db = Database(self.dbName)

        self.readCSV()

    def readCSV(self):
        status = self.db.table_read('status_db', column_values=['file_date'])
        
        csv_files = glob.glob(self.dataPath+'*.csv')

        db_connection = self.db.get_connection()
        status_db = {}
        for csv_file in csv_files:
            file_date = int(os.path.getmtime(csv_file))
            data_name = Path(csv_file).stem

            if data_name in status and file_date <= status[data_name]['file_date']: continue

            # read file into database
            data = pd.read_csv(csv_file)
            data.to_sql(data_name, con=db_connection, index=False, if_exists='replace')
            status_db[data_name] = {'file_date': file_date}

            self.logger.info('File:    Added CSV file: %s' % data_name)

        if len(status_db) > 0:
            self.db.table_write('status_db', status_db, key_name='table_name', method='update')
