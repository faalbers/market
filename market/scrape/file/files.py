from .file import File
import logging
from ...database import Database
import glob, os
from pathlib import Path
import pandas as pd
from pprint import pp
from datetime import datetime

class File_Files(File):
    dbName = 'file_files'

    @staticmethod
    def get_data_names(data_name):
        if data_name == 'all':
            return ['mic', 'country']
        return [data_name]

    def __init__(self, key_values=[], data_names=[], update = False, forced=False):
        self.db = Database(self.dbName)
        if not update: return
        self.logger = logging.getLogger('vault_multi')
        super().__init__()

        self.readCSV()
    
    def csv_preprocess(self, data, file_name):
        if file_name.startswith('SPDRS'):
            data.columns = data.iloc[0]
            data = data.iloc[1:]
        return data
    
    def readCSV(self):
        status_old = self.db.table_read('status_db')
        
        csv_files = glob.glob(self.dataPath+'*.csv')

        status_new = []
        status_new_index = []
        for csv_file in csv_files:
            file_date = int(os.path.getmtime(csv_file))
            data_name = Path(csv_file).stem

            if data_name in status_old.index and file_date <= status_old.loc[data_name, 'file_date']: continue

            # read file into database
            data = pd.read_csv(csv_file)
            data = self.csv_preprocess(data, os.path.basename(csv_file))
            self.db.table_write(data_name, data, replace=True)

            # update status
            status_new.append({'file_date': file_date})
            status_new_index.append(data_name)

            self.logger.info('File:    Added/Updated CSV file: %s' % data_name)

        if len(status_new) > 0:
            status_db = pd.DataFrame(status_new, index=status_new_index)
            status_db.index.name = 'table_name'
            self.db.table_write('status_db', status_db)

    def get_vault_data(self, data_name, columns, key_values):
        if data_name == 'mic':
            if len(columns) > 0:
                column_names = [x[0] for x in columns]
                data = self.db.table_read('ISO10383_MIC', columns=column_names)
                data = data.rename(columns={x[0]: x[1] for x in columns})
                return (data, self.db.timestamp)
            else:
                data = self.db.table_read('ISO10383_MIC')
                return data
        if data_name == 'country':
            if len(columns) > 0:
                column_names = [x[0] for x in columns]
                data = self.db.table_read('ISO3166_1', columns=column_names)
                data = data.rename(columns={x[0]: x[1] for x in columns})
                return (data, self.db.timestamp)
            else:
                data = self.db.table_read('ISO3166_1')
                return (data, self.db.timestamp)

    def get_vault_params(self, data_name):
        if data_name == 'mic':
            column_types = self.db.get_table_info('ISO10383_MIC')['columnTypes']
            return column_types
        if data_name == 'country':
            column_types = self.db.get_table_info('ISO3166_1')['columnTypes']
            return column_types
