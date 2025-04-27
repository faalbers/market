import sqlite3, json, os, glob, shutil, logging
import numpy as np
from pprint import pp
from datetime import datetime

class Database():
    sql_data_types = {
        int:  'INTEGER',
        float:  'REAL',
        bool:  'BOOLEAN',
        str: 'TEXT',
        dict: 'JSON',
        list: 'JSON',
    }
    sql_data_typesPD = {
        np.int64:  'INTEGER',
        np.float64:  'REAL',
        float:  'REAL',
        bool:  'BOOLEAN',
        str: 'TEXT',
        dict: 'JSON',
        list: 'JSON',
    }

    def __init__(self, name):
        self.name = name
        self.connection = sqlite3.connect('database/%s.db' % self.name)

    def __del__(self):
        self.connection.commit()
        self.connection.close()

    def close(self):
        self.connection.close()
        self.connection = None

    def get_connection(self):
        return self.connection
    
    def get_cursor(self):
        return self.connection.cursor()

    def commit(self):
        self.connection.commit()
    
    def backup(self):
        filename ='database/%s.db' % self.name
        filename_backup ='database/backup/%s_01.db' % self.name
        
        backup_files = glob.glob('database/backup/%s_*.db' % self.name)
        backup_files = [os.path.normpath(filename).replace('\\', '/') for filename in backup_files]
        backup_files.sort(reverse=True)
        
        if filename_backup in backup_files:
            # move files up
            for filename_old in backup_files:
                splits = filename_old.split(self.name)
                old_version = int(splits[1].strip('_').strip('.db'))
                if old_version > 4:
                    os.remove(filename_old)
                    continue
                new_version = old_version + 1
                new_version = "{:02d}".format(new_version)
                filename_new = 'database/backup/%s_%s.db' % (self.name, new_version)
                shutil.move(filename_old, filename_new)

        try:
            shutil.copyfile(filename, filename_backup)
            logger = logging.getLogger("vault_multi")
            logger.info(f"File backup from {filename} to {filename_backup}")

        except FileNotFoundError:
            pass

    def table_write_df(self, table_name, df):
        # create dtypes
        dtypes = df.dtypes
        dtypes[df.index.name] = df.index.dtype
        dtypes = dtypes.to_frame('types')
        try:
            dtypes['sql'] = dtypes['types'].apply(lambda x: self.sql_data_typesPD[x.type])
        except:
            # TODO this problem accures rarely. I don't know how to solveit yet
            print('crapped out here')
            print('df')
            print(df)
            print("dtypes['types']")
            print(dtypes['types'])
            print('self.sql_data_typesPD')
            pp(self.sql_data_typesPD)
            raise ValueError('Da Lambda crapped out')
        dtypes = dtypes['sql'].to_dict()
        dtypes[df.index.name] += ' PRIMARY KEY'

        # create table
        df.to_sql(table_name, self.connection, if_exists='replace', index=True, dtype=dtypes)

    def table_write(self, table_name, data, key_name, method='append'):
        # if data is empty, do nothing
        if len(data) == 0:
            return
        
        # expecting edit methods
        if not method in ['append', 'update', 'replace']:
            raise ValueError('Database.table_write: wrong method: %s' % method)

         # get key data type
        key_sql_data_type = None
        if isinstance(data, dict):
            for key, key_data in data.items():
                key_sql_data_type = self.sql_data_types[type(key)]
                break
        elif isinstance(data, list):
            key_sql_data_type = self.sql_data_types[type(data[0])]
        else:
            raise ValueError('Database.table_write: unknown data type: %s' % type(data))
        if key_sql_data_type == None:
            raise ValueError('Database.table_write: key has unknown SQL data type')

        cursor = self.connection.cursor()
        # only create table if not exist, add primary key column
        cursor.execute("CREATE TABLE IF NOT EXISTS %s  ([%s] %s PRIMARY KEY)" % (table_name, key_name, key_sql_data_type))

        # get table info
        table_info = self.get_table_info(table_name)
        if not key_name in table_info['primaryKeyColumns']:
            raise ValueError('Database.table_write: key name not in existing table: %s' % key_name)
        table_columns = set(table_info['columns'])

        # table indices as we build, maybe later implement with proc
        key_values = cursor.execute("SELECT %s FROM %s" % (key_name, table_name)).fetchall()
        key_values = set([x[0] for x in key_values])

        # set data columns structure
        column_sql_types = {}
        if isinstance(data, dict):
            for key_value, key_data in data.items():
                for column_name, value in key_data.items():
                    if value == None: continue
                    column_sql_types[column_name] = self.sql_data_types[type(value)]

        # add columns if needed
        columns_to_add = set(column_sql_types.keys()).difference(table_columns)
        for column_name in columns_to_add:
            cursor.execute("ALTER TABLE %s ADD COLUMN [%s] %s" % (table_name, column_name, column_sql_types[column_name]))

        columns = [key_name]+list(column_sql_types.keys())
        values_append = []
        values_update = []
        drop_keys = set()
        if isinstance(data, dict):
            for key_value, key_data in data.items():
                if key_value in key_values:
                    # no need to append since it already exists
                    if method == 'append': continue
                    # drop key before appending it back
                    elif method == 'replace': drop_keys.add(key_value)

                row_values = [None]*len(columns)
                row_values[0] = key_value
                c_index = 1
                for column_name in columns[1:]:
                    if column_name in key_data:
                        value = key_data[column_name]
                        if column_sql_types[column_name] == 'JSON':
                            value = json.dumps(value)
                        row_values[c_index] = value
                    c_index += 1
                if method in ['append', 'replace']: 
                    values_append.append(tuple(row_values))
                else:
                    if key_value in key_values:
                        values_update.append(row_values)
                    else:
                        values_append.append(tuple(row_values))
        elif isinstance(data, list):
            for key_value in data:
                if key_value in key_values:
                    # no need to append since it already exists
                    if method == 'append': continue
                row_values = [key_value]
                
                if method == 'append': 
                    values_append.append(tuple(row_values))

        # drop rows
        if len(drop_keys) > 0:
            value_holder_string = ','.join(['?']*len(drop_keys))
            exec_string = "DELETE FROM '%s' WHERE [%s] IN (%s)" % (table_name, key_name, value_holder_string)
            cursor.execute(exec_string, tuple(drop_keys))

        # append or update
        if len(values_append) > 0:
            columns_string = ','.join('[%s]'%x for x in columns)
            value_holder_string = ','.join(['?']*len(columns))
            exec_string = "INSERT OR IGNORE INTO %s (%s) VALUES (%s)" % (table_name, columns_string, value_holder_string)
            cursor.executemany(exec_string, values_append)
        if len(values_update) > 0:
            for values in values_update:
                update_columns = []
                update_values = []
                c_index = 1
                for value in values[1:]:
                    if value != None:
                        update_columns.append(columns[c_index])
                        update_values.append(value)
                    c_index += 1
                columns_string = ','.join('[%s]'%x for x in update_columns)
                value_holder_string = ','.join(['?']*len(update_columns))
                exec_string = "UPDATE %s SET (%s) = (%s) WHERE [%s] = '%s'"  % (table_name, columns_string, value_holder_string, columns[0], values[0])
                cursor.execute(exec_string, tuple(update_values))
        
        cursor.close()

    def table_read(self, table_name, key_values=[], column_values=[], max_column=None):
        # There is a limit on SQL entries for key_values
        key_values_limit = 30000
        key_values = list(key_values)
        if len(key_values) > key_values_limit:
            # cut key_values into chunks and combine results
            chunks = {}
            limit_idx = key_values_limit
            while limit_idx < (len(key_values)+1):
                key_values_chunk = key_values[limit_idx-key_values_limit:limit_idx]
                chunk = self.table_read_chunk(table_name, key_values_chunk, column_values, max_column)
                chunks = {**chunks, **chunk}
                limit_idx += key_values_limit
            left_idx = len(key_values) % key_values_limit
            if left_idx > 0:
                key_values_chunk = key_values[-left_idx:]
                chunk = self.table_read_chunk(table_name, key_values_chunk, column_values, max_column)
                chunks = {**chunks, **chunk}
            return chunks
        else:
            # do the whole thing
            return self.table_read_chunk(table_name, key_values, column_values, max_column)
    
    def table_read_chunk(self, table_name, key_values=[], column_values=[], max_column=None):
        # get table info
        table_info = self.get_table_info(table_name)
        if not table_info: return {}
        # get list of columns without the key columns
        table_columns = table_info['columns']
        column_values = set(column_values)
        
        # get key column if any and construct table_columns
        key_column = None
        if len(table_info['primaryKeyColumns']) > 0:
            key_column = table_info['primaryKeyColumns'][0]
        
        # create selection exec string
        if len(column_values) == 0:
            # we are selecting all columns
            columns_string = '*'
        else:
            # handle only columns that exist
            columns = column_values.intersection(table_columns)
            columns_string = ','.join(['[%s]'%x for x in columns])
            # return empty if no columns to be searched
            if columns_string == '': return {}
            if key_column and not key_column in columns:
                columns_string = '[%s],'%key_column+columns_string
        exec_string = "SELECT %s FROM '%s'" % (columns_string, table_name)
        
        execution = None
        cursor = self.connection.cursor()
        if key_column and len(key_values) > 0:
            # we will only get the ones with the key values
            value_holder_string = ','.join(['?']*len(key_values))
            exec_string += " WHERE [%s] IN (%s)" % (key_column, value_holder_string)
            if max_column:
                exec_string += " ORDER BY [%s] DESC LIMIT 1" % max_column
            execution = cursor.execute(exec_string, tuple(key_values))
        else:
            # we are getting them all
            if max_column:
                exec_string += " ORDER BY [%s] DESC LIMIT 1" % max_column
            execution = cursor.execute(exec_string)
        data_columns = [x[0] for x in execution.description]
        data_columns_sql_types = []
        for column in data_columns:
            data_columns_sql_types.append(table_info['columnTypes'][column])
        data_values = execution.fetchall()
        cursor.close()

        # retrieve data in dictionary or list
        data_dictionary = {}
        data_list = []
        key_column_index = -1
        if key_column:
            key_column_index = data_columns.index(key_column)
        # print(data_columns)
        # print(data_columns_sql_types)
        # print(key_column_index)

        for row_values in data_values:
            # create dict out of row data
            row_data = dict(zip(data_columns, row_values))

            # handle JSON
            json_indices = [i for i, s in enumerate(data_columns_sql_types) if s == 'JSON']
            for json_index in json_indices:
                if row_data[data_columns[json_index]] != None:
                    row_data[data_columns[json_index]] = json.loads(row_data[data_columns[json_index]])

            # get key value if needed
            if key_column_index != -1: key_value = row_values[key_column_index]

            # only keep row data that is requested
            if len(column_values) > 0:
                row_data = {k: v for k, v in row_data.items() if k in column_values}
         
            if key_column_index != -1:
                data_dictionary[key_value] = row_data
            else:
                data_list.append(row_data)

        if key_column:
            return data_dictionary
        else:
            return data_list

    def get_table_info(self, table_name):
        if not self.table_exists(table_name): return None

        table_info = {
            'columns': [],
            'primaryKeyColumns': [],
            'columnTypes': {},
            'rows': 0,
            'sql': '',
        }

        cursor = self.connection.cursor()
        table_columns = cursor.execute("PRAGMA table_info(%s)" % table_name).fetchall()
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

    def table_exists(self, table_name):
        return table_name in self.get_table_names()

    def get_table_names(self):
        cursor = self.connection.cursor()
        names = [ x[0] for x in cursor.execute("SELECT name FROM sqlite_schema WHERE type='table'")]
        cursor.close()
        return names

    def get_table_column_names(self, table_name):
        if not self.table_exists(table_name): return []
        cursor = self.connection.cursor()
        table_info = cursor.execute("PRAGMA table_info(%s)" % table_name).fetchall()
        cursor.close()
        return [x[1] for x in table_info]

    def table_drop(self, table_name):
        cursor = self.connection.cursor()
        cursor.execute("DROP TABLE IF EXISTS '%s'" % table_name)
        cursor.close()

    def vacuum(self):
        self.backup()
        cursor = self.connection.cursor()
        cursor.execute("VACUUM")
        cursor.close()
        