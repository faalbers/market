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
        
        backup_files = glob.glob('database/backup/%s_*' % self.name)
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

    def table_read(self, table_name, key_values=[], columns=[], handle_key_values=True, max_column=None):
        # print()
        # print(table_name)
        # print(key_values)
        # print(columns)
        # print(handle_key_values)
        
        # get table info
        table_info = self.get_table_info(table_name)
        if not table_info: return {}
        table_columns = set(table_info['columns']).difference(set(table_info['primaryKeyColumns']))
        
        # if we need to handle key values but there are none, return empty
        if handle_key_values:
            if len(table_info['primaryKeyColumns']) > 0:
                key_column = table_info['primaryKeyColumns'][0]
            else:
                return {}
        
        # get data
        if len(columns) == 0:
            columns_string = '*'
        else:
            # handle only columns that exist
            columns = set(columns).intersection(table_columns)
            columns_string = ','.join(['[%s]'%x for x in columns])
            # return empty if no columns to be searched
            if columns_string == '': return {}
            if handle_key_values:
                columns_string = '[%s],'%key_column+columns_string
        exec_string = "SELECT %s FROM '%s'" % (columns_string, table_name)
        
        execution = None
        cursor = self.connection.cursor()
        if handle_key_values and len(key_values) > 0:
            value_holder_string = ','.join(['?']*len(key_values))
            exec_string += " WHERE [%s] IN (%s)" % (key_column, value_holder_string)
            if max_column:
                exec_string += " ORDER BY [%s] DESC LIMIT 1" % max_column
            execution = cursor.execute(exec_string, tuple(key_values))
        else:
            if max_column:
                exec_string += " ORDER BY [%s] DESC LIMIT 1" % max_column
            execution = cursor.execute(exec_string)
        data_columns = [x[0] for x in execution.description]
        data_columns_sql_types = []
        for column in data_columns:
            data_columns_sql_types.append(table_info['columnTypes'][column])
        data_values = execution.fetchall()
        cursor.close()

        # retrieve data in dictionary
        data_dictionary = {}
        data_list = []
        for row_values in data_values:
            if handle_key_values:
                rowData = data_dictionary[row_values[0]] = {}
                c_index = 1
                row_values = row_values[1:]
            else:
                rowData = {}
                c_index = 0
            for value in row_values:
                if value != None:
                    if data_columns_sql_types[c_index] == 'JSON':
                        value = json.loads(value)
                    rowData[data_columns[c_index]] = value
                c_index += 1
            if not handle_key_values:
                data_list.append(rowData)

        if handle_key_values:
            return data_dictionary
        else:
            return data_list

    def get_table_info(self, table_name):
        if not self.tableExists(table_name): return None

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
            # print(table_column)
            table_info['columns'].append(table_column[1])
            if table_column[5]: table_info['primaryKeyColumns'].append(table_column[1])
            table_info['columnTypes'][table_column[1]] = table_column[2]
        table_info['sql'] = sql[0]
        table_info['rows'] = row_count[0]

        return table_info

    def tableExists(self, table_name):
        return table_name in self.get_table_names()

    def get_table_names(self):
        cursor = self.connection.cursor()
        names = [ x[0] for x in cursor.execute("SELECT name FROM sqlite_schema WHERE type='table'")]
        cursor.close()
        return names
