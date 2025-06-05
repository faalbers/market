import sqlite3, os, glob, shutil, json
import pandas as pd
from pprint import pp
import numpy as np
from multiprocessing import Pool

class Database():
    sql_types = {
        np.int64:  'INTEGER',
        np.float64:  'REAL',
        np.bool_:  'BOOLEAN',
        # int:  'INTEGER',
        # float:  'REAL',
        # bool:  'BOOLEAN',
        # str: 'TEXT',
        # dict: 'JSON',
        # list: 'JSON',
    }

    def __sql_type(self, column):
        column_type = column.dtype.type
        if column_type == np.object_:
            if isinstance(column, pd.Index): return 'TEXT'
            data_types = set(column.apply(type).tolist())
            if len(data_types.difference(set([str, float, type(None)]))) == 0: return 'TEXT'
            if len(data_types.difference(set([bool, float]))) == 0: return 'BOOLEAN'
            if len(data_types.difference(set([list, dict, float, type(None)]))) == 0: return 'JSON'
            raise ValueError('Unknown data types: %s' % data_types)

        return self.sql_types[column_type]

    def __init__(self, name, new=False):
        self.name = name
        file_path = 'database/%s.db' % self.name
        if new and os.path.exists(file_path): os.remove(file_path)
        self.connection = sqlite3.connect(file_path)
        self.timestamp = os.path.getmtime(file_path)

    def __del__(self):
        self.connection.commit()
        self.connection.close()

    def close(self):
        self.connection.close()
        self.connection = None

    def commit(self):
        self.connection.commit()
    
    def backup(self):
        filename ='database/%s.db' % self.name
        filename_backup ='database/backup/%s_01.db' % self.name
        
        backup_files = glob.glob('database/backup/%s_0*.db' % self.name)
        backup_files = [os.path.normpath(filename).replace('\\', '/') for filename in backup_files]
        backup_files.sort(reverse=True)
        
        if filename_backup in backup_files:
            # move files up
            for filename_old in backup_files:
                splits = filename_old.split(self.name)
                old_version = int(splits[1].strip('_').strip('.db'))
                # if old_version > 4:
                if old_version > 1:
                    os.remove(filename_old)
                    continue
                new_version = old_version + 1
                new_version = "{:02d}".format(new_version)
                filename_new = 'database/backup/%s_%s.db' % (self.name, new_version)
                shutil.move(filename_old, filename_new)

        try:
            shutil.copyfile(filename, filename_backup)
            return 'File backup from %s to %s' % (filename, filename_backup)
        except FileNotFoundError:
            return 'File backup from %s failed' % filename

    def get_table_names(self):
        cursor = self.connection.cursor()
        names = [ x[0] for x in cursor.execute("SELECT name FROM sqlite_schema WHERE type='table'")]
        cursor.close()
        return sorted(names)

    def get_table_info(self, table_name):
        table_info = {
            'columns': [],
            'primaryKeyColumns': [],
            'columnTypes': {},
            'rows': 0,
            'sql': '',
        }

        cursor = self.connection.cursor()
        table_columns = cursor.execute("PRAGMA table_info('%s')" % table_name).fetchall()
        if len(table_columns) == 0: return {}

        row_count = cursor.execute("SELECT COUNT(*) FROM %s" % table_name).fetchone()
        sql = cursor.execute("SELECT sql FROM sqlite_schema WHERE type='table' AND name='%s'" % table_name).fetchone()
        cursor.close()

        for table_column in table_columns:
            table_info['columns'].append(table_column[1])
            if table_column[5]: table_info['primaryKeyColumns'].append(table_column[1])
            table_info['columnTypes'][table_column[1]] = table_column[2]
        table_info['sql'] = sql[0]
        table_info['rows'] = row_count[0]

        return table_info

    def table_keys(self, table_name):
        cursor = self.connection.cursor()

        # get table info
        table_info = cursor.execute("PRAGMA table_info('%s')" % table_name).fetchall()
        if len(table_info) == 0:
            cursor.close()
            return []
        
        # get primary key columns
        primary_key_columns = [x[1] for x in table_info if x[5] == 1]
        if len(primary_key_columns) == 0:
            cursor.close()
            return []

        key_name = primary_key_columns[0]
        key_values = cursor.execute("SELECT [%s] FROM %s" % (primary_key_columns[0], table_name)).fetchall()
        cursor.close()
        return sorted([x[0] for x in key_values])

    def table_read(self, table_name, keys=[], columns=[]):
        # keys = []
        cursor = self.connection.cursor()

        # get table info
        self.commit()
        table_info = cursor.execute("PRAGMA table_info('%s')" % table_name).fetchall()
        if len(table_info) == 0:
            cursor.close()
            # nothing to retrieve
            return pd.DataFrame()
        all_columns = [x[1] for x in table_info]
        json_columns = [x[1] for x in table_info if x[2] == 'JSON']
        primary_key_columns = [x[1] for x in table_info if x[5] == 1]
        
        # handle column selection
        exec_string = 'SELECT *'
        if len(columns) > 0:
            if len(primary_key_columns) > 0 and not primary_key_columns[0] in columns:
                columns = [primary_key_columns[0]] + columns
            columns = [x for x in columns if x in all_columns]
            columns_string = ','.join(['[%s]'%x for x in columns])
            exec_string = 'SELECT %s' % columns_string
        exec_string += " FROM '%s'" % table_name
        
        # handle keys selection
        if len(keys) > 0 and len(primary_key_columns) > 0:
            if len(keys) <= 30000:
                exec_string += " WHERE [%s] IN (%s)" % (primary_key_columns[0], ','.join(['?']*len(keys)))
                execution = cursor.execute(exec_string, tuple(keys))
            else:
                execution = cursor.execute(exec_string)
        else:
            execution = cursor.execute(exec_string)

        # fetch data
        table_columns = [x[0] for x in execution.description]
        table_data = execution.fetchall()
        cursor.close()
        table_data = pd.DataFrame(table_data, columns=table_columns)

        # handle primary key
        if len(primary_key_columns) > 0:
            table_data.set_index(primary_key_columns[0], inplace=True)
            table_data = table_data.sort_index()
            if len(keys) > 30000:
                table_data = table_data[table_data.index.isin(keys)]

        # change json to data if needed
        for column in table_data.columns:
            if column not in json_columns: continue
            table_data[column] = table_data[column].apply(lambda x: json.loads(x) if pd.notna(x) else x)

        return table_data

    def table_write(self, table_name, df, replace=False, update=True):
        # since we are manipulating df, make a copy
        df = df.copy()
        if df.empty: return

        # check index
        index_name = df.index.name
        index = False
        if index_name != None:
            if not df.index.is_unique: raise ValueError('Index is not unique')
            if index_name in df.columns: raise ValueError('Index name same as colmn name')
            index = True

        # drop column where all values are nan
        df.dropna(axis=1, how='all', inplace=True)

        # get column types
        dtypes = {}
        if index:
            dtypes[index_name] = self.__sql_type(df.index) + ' PRIMARY KEY'
        for column in df.columns:
            dtypes[column] = self.__sql_type(df[column])

        # dump JSON columns if needed
        for column, dtype in dtypes.items():
            if dtype != 'JSON': continue
            df[column] = df[column].apply(lambda x: json.dumps(x) if not isinstance(x, type(None)) else x)

        cursor = self.connection.cursor()

        # if force replace, no need to do all below
        if replace:
            if index:
                df.to_sql(table_name, self.connection, if_exists='replace', index=True, dtype=dtypes)
            else:
                df.to_sql(table_name, self.connection, if_exists='replace', index=False, dtype=dtypes)
            return

        # we are reading data befor writing, so we commit first
        self.commit()

        # get table info
        table_info = cursor.execute("PRAGMA table_info('%s')" % table_name).fetchall()
        if len(table_info) == 0:
            # it's a new on, just use to_sql
            cursor.close()
            if index:
                df.to_sql(table_name, self.connection, if_exists='replace', index=True, dtype=dtypes)
            else:
                df.to_sql(table_name, self.connection, if_exists='replace', index=False, dtype=dtypes)
            return
        
        # check if we need to add columns
        table_columns = [x[1] for x in table_info]
        for column_name, dtype in dtypes.items():
            if column_name in table_columns: continue
            cursor.execute("ALTER TABLE %s ADD COLUMN [%s] %s" % (table_name, column_name, dtype))

        if index:
            # handle dataframe with index
            primary_key_columns = [x[1] for x in table_info if x[5] == 1]
            if index_name in primary_key_columns:
                # find indices to append or update
                key_values = cursor.execute("SELECT [%s] FROM '%s'" % (index_name, table_name)).fetchall()
                key_values = [x[0] for x in key_values]
                df_append = df[~df.index.isin(key_values)]
                df_update = df[df.index.isin(key_values)]
                if not df_append.empty:
                    # handle appends
                    df_append.reset_index(inplace=True)
                    columns_string = ','.join('[%s]'%x for x in df_append.columns)
                    value_holder_string = ','.join(['?']*len(df_append.columns))
                    exec_string = "INSERT OR IGNORE INTO '%s' (%s) VALUES (%s)" % (table_name, columns_string, value_holder_string)
                    values = df_append.values.tolist()
                    cursor.executemany(exec_string, values)
                if not df_update.empty and update:
                    # handle updates
                    for index, row in df_update.iterrows():
                        # only update non empty values
                        row = row.dropna()
                        if len(row) == 0: continue
                        columns_string = ','.join('[%s]'%x for x in row.index)
                        value_holder_string = ','.join(['?']*row.shape[0])
                        exec_string = "UPDATE '%s' SET (%s) = (%s) WHERE [%s] = '%s'"  % (table_name, columns_string, value_holder_string, index_name, index)
                        # print(tuple(row.tolist()))
                        cursor.execute(exec_string, tuple(row.tolist()))
        else:
            # just append them all
            df.to_sql(table_name, self.connection, if_exists='append', index=False, dtype=dtypes)
        cursor.close()

    def table_write_reference(self, symbol, reference, df, replace=False, update=True):
        # make reference table name
        reference_name = reference + '_' + symbol
        self.table_write(reference_name, df, replace=replace, update=update)
        table_reference = pd.DataFrame([{reference: reference_name}], index=[symbol])
        table_reference.index.name = 'symbol'
        self.table_write('table_reference', table_reference)

    def table_rename(self, old_table_name, new_table_name):
        cursor = self.connection.cursor()
        cursor.execute("ALTER TABLE '%s' RENAME TO '%s'" % (old_table_name, new_table_name))
        cursor.close()

    def table_delete(self, table_name):
        cursor = self.connection.cursor()
        cursor.execute("DROP TABLE '%s'" % table_name)
        cursor.close()
        
    def write_status(self, symbol, status):
        status_df = pd.DataFrame([status], index=[symbol])
        status_df.index.name = 'symbol'
        self.table_write('status_db', status_df)
        
    @staticmethod
    def reference_chunk(data):
        keys = data[0]
        columns = data[1]
        index_date = data[2]
        db_name = data[3]
        db = Database(db_name)

        timeseries = {}
        for key, table_name in keys.items():
            df = db.table_read(table_name, columns=columns)
            if index_date:
                df.index = pd.to_datetime(df.index, unit='s')
                df.index.name = 'date'
            timeseries[key] = df
        
        return timeseries

    def timeseries_read(self, reference, keys=[], columns=[], index_date=True):
        return self.table_read_reference(reference, keys=keys, columns=columns, index_date=index_date)

    def table_read_reference(self, reference, keys=[], columns=[], index_date=False):
        reference_table = self.table_read('table_reference', keys=keys, columns=[reference])[reference]
        
        timeseries = {}
        if reference_table.shape[0] < 1200:
            for key, table_name in reference_table.items():
                df = self.table_read(table_name, columns=columns)
                if index_date:
                    df.index = pd.to_datetime(df.index, unit='s')
                    df.index.name = 'date'
                timeseries[key] = df
            return timeseries
        
        # get with multi process
        # gather symbol chunks based on cpu count
        cpus = 8
        keys = list(reference_table.index)
        keys_limit = int(len(keys)/cpus)
        if len(keys) % cpus > 0: keys_limit += 1
        key_chunks = []
        limit_idx = keys_limit
        while limit_idx < (len(keys)+1):
            key_chunk = keys[limit_idx-keys_limit:limit_idx]
            dict_chunk = {key: reference_table[key] for key in key_chunk}
            key_chunks.append((dict_chunk, columns, index_date, self.name))
            limit_idx += keys_limit
        left_idx = len(keys) % keys_limit
        if left_idx > 0:
            key_chunk = keys[-left_idx:]
            dict_chunk = {key: reference_table[key] for key in key_chunk}
            key_chunks.append((dict_chunk, columns, index_date, self.name))
        
        with Pool(processes=cpus) as pool:
            results = pool.map(Database.reference_chunk, key_chunks)
            for result in results:
                timeseries.update(result)
        
        return timeseries

    def table_exists(self, table_name):
        return table_name in self.get_table_names()

    def vacuum(self):
        self.backup()
        cursor = self.connection.cursor()
        cursor.execute("VACUUM")
        cursor.close()
