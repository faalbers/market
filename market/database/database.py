import sqlite3, json
import numpy as np

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
        self.connection = sqlite3.connect('database/%s.db' % name)

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

    def table_write(self, table_name, data, key_name, method='append'):
        # make sure it is a dict
        if not isinstance(data, dict):
            raise TypeError('Database.table_write: wrong datatype: %s' % type(data))
        # if data is empty, do nothing
        if len(data) == 0:
            return
        
        # expecting edit methods
        if not method in ['append', 'update', 'replace']:
            raise ValueError('Database.table_write: wrong method: %s' % method)

         # get key data type
        key_sql_data_type = None
        for key, key_data in data.items():
            key_sql_data_type = self.sql_data_types[type(key)]
        if key_sql_data_type == None:
            raise ValueError('Database.table_write: data is empty')

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
