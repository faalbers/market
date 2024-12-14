from ..scrape import *
from pprint import pp

class Catalog():
    def __init__(self):
        pass

    def get_catalog(self, catalog_name):
        if catalog_name in self.catalog:
            return self.catalog[catalog_name]
        return {}

    @staticmethod
    def merge(self, data, db=None, allow_collision=False):
        merge_types = set()
        for merge_name, merge_data in data.items():
            merge_types.add(type(merge_data))
        
        if len(merge_types) > 1:
            raise ValueError('Catalog.merge: mixed merge types: %s' % merge_types)
        
        merge_type = merge_types.pop()
        new_list = []
        for merge_name in list(data.keys()):
            if merge_type == dict:
                for key_name, key_data in data.pop(merge_name).items(): 
                    if not key_name in data:
                        data[key_name] = key_data
                    elif not allow_collision:
                        key_name_collision = set(data[key_name].keys()).intersection(key_data.keys())
                        if len(key_name_collision) > 0:
                            raise ValueError('Catalog.merge: key names collision: %s' % key_name_collision)
                        data[key_name] = {**data[key_name], **key_data}
            elif merge_type == list:
                new_list += data[merge_name]
        
        if merge_type == list: data = new_list

        return data
    
    @staticmethod
    def reference(self, data, db, timestamps_table=None):
        referenced_data = {}
        for table_reference, reference_data in data.items():
            for key_value, key_table_reference in reference_data.items():
                referenced_data[key_value] = {}
                for reference_name, reference_table in key_table_reference.items():
                    if timestamps_table:
                        timestamps = db.table_read(reference_table).keys()
                        referenced_data[key_value][reference_name] = db.table_read(timestamps_table, key_values=timestamps)
                    else:
                        referenced_data[key_value][reference_name] = db.table_read(reference_table)
        return referenced_data

    @staticmethod
    def test_proc(self, data, db=None):
        print(db)
        pp(data.keys())
        return data

    catalog = {
        'symbols': {
            'info': 'get all symbols in our scrapes',
            'post_procs': [[merge, {}]],
            'sets': {
                'Yahoo_Quote': {
                    'scrapes': {
                        Yahoo_Quote: {
                            'post_procs': [[merge, {'allow_collision': True}]],
                            'tables': {
                                'all': {
                                    'column_settings': [
                                        ['symbol', 'symbol'],
                                    ],
                                },
                            },
                        },
                    },
                },
                'Yahoo_Chart': {
                    'scrapes': {
                        Yahoo_Chart: {
                            'post_procs': [[merge, {}]],
                            'tables': {
                                'table_reference': {
                                    'column_settings': [
                                        ['symbol', 'symbol'],
                                    ],
                                },
                            },
                        },
                    },
                },
            },
        },
       'us_symbols': {
            'info': 'get all symbols for market and locale',
            # 'post_procs': [[merge, {}]],
            'sets': {
                'symbols': {
                    'post_procs': [[merge, {}]],
                    'scrapes': {
                        FMP_Stocklist: {
                            'tables': {
                                'stocklist': {
                                    'column_settings': [
                                        ['exchangeShortName', 'acronym'],
                                    ],
                                },
                            },
                        },
                        Polygon_Tickers: {
                            'tables': {
                                'tickers': {
                                    'column_settings': [
                                        ['locale', 'locale'],
                                        ['market', 'market'],
                                    ],
                                },
                            },
                        },
                    },
                },
                'iso': {
                    'post_procs': [[merge, {}]],
                    'scrapes': {
                        File_Files: {
                            'post_procs': [[merge, {}]],
                            'tables': {
                                'ISO10383_MIC': {
                                    'column_settings': [
                                        ['ACRONYM', 'acronym'],
                                        ['ISO COUNTRY CODE (ISO 3166)', 'cc'],
                                    ],
                                },
                            },
                        },
                    },
                },
            },
        },
        'update_nightly': {
            'info': 'update all scrapes',
            'sets': {
                'all': {
                    'scrapes': {
                        Yahoo_Quote: {'tables': {'all': {},}},
                        Yahoo_Chart: {'tables': {'all': {},}},
                        Finviz_Ticker_News: {'tables': {'all': {},}},
                        Polygon_News: {'tables': {'all': {},}},
                        File_Files: {'tables': {'all': {},}},
                    },
                },
            },
        },
        'update_symbols': {
            'info': 'update all scrapes with symbol kewy values',
            'sets': {
                'all': {
                    'scrapes': {
                        Yahoo_Quote: {'tables': {'all': {},}},
                        Yahoo_Chart: {'tables': {'all': {},}},
                        Finviz_Ticker_News: {'tables': {'all': {},}},
                    },
                },
            },
        },
        'news': {
            'info': 'news data',
            'post_procs': [[merge, {}]],
            'sets': {
                'news': {
                    'post_procs': [[merge, {}]],
                    'scrapes': {
                        Finviz_Ticker_News: {
                            'post_procs': [[reference, {}]],
                            'tables': {
                                'table_reference': {
                                    'column_settings': [
                                        ['news', 'news_finviz'],
                                    ],
                                },
                            },
                        },
                        Polygon_News: {
                            'post_procs': [[reference, {'timestamps_table': 'news_articles'}]],
                            'tables': {
                                'table_reference': {
                                    'column_settings': [
                                        ['news', 'news_polygon'],
                                    ],
                                },
                            },
                        },
                    },
                },
            },
        },
    }
