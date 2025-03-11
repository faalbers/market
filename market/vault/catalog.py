from ..scrape import *
from ..database import Database
from pprint import pp
import pandas as pd
from multiprocessing import Pool
import math

class Catalog():
    def __init__(self):
        pass

    def get_catalog(self, catalog_name):
        if catalog_name in self.catalog:
            return self.catalog[catalog_name]
        return {}

    @staticmethod
    def merge(self, data, db=None, allow_collision=False):
        if len(data) == 0: return data
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
    def reference_multi(params):
        key_table_reference = params[0]
        db_name = params[1]
        db = Database(db_name)
        data = {}
        for key_value, table_name in key_table_reference.items():
            data[key_value] = db.table_read(table_name)
        return data

    @staticmethod
    def reference(self, data, db, timestamps_table=None):
        # get referenced tables for key value
        cpus = 8
        new_data = {}
        for table_reference, reference_data in data.items():
            reference_df = pd.DataFrame(reference_data).T
            for reference_name, reference_tables in reference_df.items():
                # make a dataframe to easily chunk it for multiprocessing
                reference_data = {}
                if reference_tables.shape[0] > 105:
                    # only multiprocessing if more the 105 references
                    chunk_size = math.ceil(reference_tables.shape[0] / cpus)
                    chunks = [(reference_tables.iloc[i:i+chunk_size], db.name) for i in range(0, reference_tables.shape[0], chunk_size)]
                    with Pool(processes=cpus) as pool:
                        results = pool.map(Catalog.reference_multi, chunks)
                        for result in results:
                            for key_value, key_table_reference in result.items():
                                reference_data[key_value] = key_table_reference
                else:
                    # handle serial processing
                    for key_value, key_table_reference in reference_tables.items():
                        reference_data[key_value] = db.table_read(key_table_reference)
                new_data[reference_name] = reference_data
        return new_data
    
    @staticmethod
    def test_proc(self, data, db=None):
        print(db)
        pp(data.keys())
        return data

    catalog = {
        'update_yf': {
            'info': 'chart test info',
            'sets': {
                'YahooF_Chart': {
                    'scrapes': {
                        # YahooF_Chart: {'tables': {'all': {},}},
                        YahooF_Info: {'tables': {'all': {},}},
                    },
                },
            },
        },
        'chart': {
            'info': 'chart info',
            'post_procs': [[merge, {}]],
            'sets': {
                'Yahoo_Chart': {
                    'post_procs': [[merge, {}]],
                    'scrapes': {
                        Yahoo_Chart: {
                            'post_procs': [[reference, {}]],
                            'tables': {
                                'table_reference': {
                                    'column_settings': [
                                        ['chart', 'chart'],
                                    ],
                                },
                            },
                        },
                    },
                },
            },
        },
        'price': {
            'info': 'price info',
            'post_procs': [[merge, {}]],
            'sets': {
                'Yahoo_Quote': {
                    'post_procs': [[merge, {}]],
                    'scrapes': {
                        Yahoo_Quote: {
                            'post_procs': [[merge, {}]],
                            'tables': {
                                'price': {
                                    'column_settings': [
                                        ['regularMarketPrice', 'price'],
                                    ],
                                },
                            },
                        },
                    },
                },
            },
        },
        'profile': {
            'info': 'get all symbols in our scrapes',
            'post_procs': [[merge, {}]],
            'sets': {
                'Yahoo_Quote': {
                    'post_procs': [[merge, {}]],
                    'scrapes': {
                        Yahoo_Quote: {
                            'post_procs': [[merge, {}]],
                            'tables': {
                                'quoteType': {
                                    'column_settings': [
                                        ['longName', 'name'],
                                    ],
                                },
                            },
                        },
                    },
                },
            },
        },
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
        'update_test': {
            'info': 'update all scrapes',
            'sets': {
                'all': {
                    'scrapes': {
                        Polygon_News: {'tables': {'all': {},}},
                    },
                },
            },
        },
        'update_nightly': {
            'info': 'update all scrapes',
            'sets': {
                'all': {
                    'scrapes': {
                        # Yahoo_Quote: {'tables': {'all': {},}},
                        # Yahoo_Chart: {'tables': {'all': {},}},
                        Yahoo_Timeseries: {'tables': {'all': {},}},
                        # Finviz_Ticker_News: {'tables': {'all': {},}},
                        # Polygon_News: {'tables': {'all': {},}},
                        # Fred: {'tables': {'all': {},}},
                        # File_Files: {'tables': {'all': {},}},
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
                            # 'post_procs': [[reference, {'timestamps_table': 'news_articles'}]],
                            'post_procs': [[reference, {}]],
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
        'all_tickers': {
            'info': 'all info',
            'sets': {
                'Yahoo': { 'scrapes': {
                        Yahoo_Quote: { 'tables': { 'all': { 'column_settings': [ ['all', ''], ], }, }, },
                        # Yahoo_Chart: {
                        #     'post_procs': [[reference, {}]],
                        #     'tables': { 'table_reference': { 'column_settings': [ ['chart', 'chart'], ], }, },
                        # },
                    },
                },
                # 'FMP': { 'scrapes': {
                #         FMP_Stocklist: { 'tables': { 'all': { 'column_settings': [ ['all', ''], ], }, }, },
                #     },
                # },
                # 'Polygon': { 'scrapes': {
                #         Polygon_Tickers: { 'tables': { 'all': { 'column_settings': [ ['all', ''], ], }, }, },
                #         Polygon_News: {
                #             'post_procs': [[reference, {}]],
                #             'tables': { 'table_reference': { 'column_settings': [ ['news', 'news_polygon'], ], }, },
                #         },
                #     },
                # },
                # 'Finviz': { 'scrapes': {
                #         Finviz_Ticker_News: {
                #             'post_procs': [[reference, {}]],
                #             'tables': { 'table_reference': { 'column_settings': [ ['news', 'news_finviz'], ], }, },
                #         },
                #     },
                # },
            },
        },
        'all_other': {
            'info': 'all info',
            'sets': {
                'File': { 'scrapes': {
                        File_Files: { 'tables': { 'all': { 'column_settings': [ ['all', ''], ], }, }, },
                    },
                },
                'Fred': { 'scrapes': {
                        Fred: { 'tables': { 'all': { 'column_settings': [ ['all', ''], ], }, }, },
                    },
                },
            },
        },
        'revenue_growth': {
            'info': 'get revenue data',
            'post_procs': [[merge, {}]],
            'sets': {
                'Yahoo_Quote': {
                    'post_procs': [[merge, {}]],
                    'scrapes': {
                        Yahoo_Quote: {
                            # 'post_procs': [[merge, {}]],
                            'tables': {
                                'financialData': {
                                    'column_settings': [
                                        ['revenueGrowth', 'revenueGrowth'],
                                        ['revenuePerShare', 'revenuePerShare'],
                                        ['totalRevenue', 'totalRevenue'],
                                        ['earningsGrowth', 'earningsGrowth'],
                                    ],
                                },
                                'incomeStatementHistory': {
                                    'column_settings': [
                                        ['incomeStatementHistory', 'incomeStatementHistory'],
                                    ],
                                },
                                'incomeStatementHistoryQuarterly': {
                                    'column_settings': [
                                        ['incomeStatementHistory', 'incomeStatementHistory'],
                                    ],
                                },
                                'calendarEvents': {
                                    'column_settings': [
                                        ['earnings', 'earnings'],
                                    ],
                                },
                                'earnings': {
                                    'column_settings': [
                                        ['financialsChart', 'financialsChart'],
                                    ],
                                },
                                'earningsTrend': {
                                    'column_settings': [
                                        ['trend', 'trend'],
                                    ],
                                },
                                'indexTrend': {
                                    'column_settings': [
                                        ['estimates', 'estimates'],
                                    ],
                                },
                                'defaultKeyStatistics': {
                                    'column_settings': [
                                        ['earningsQuarterlyGrowth', 'earningsQuarterlyGrowth'],
                                    ],
                                },
                            },
                        },
                        Yahoo_Timeseries: {
                            # 'post_procs': [[merge, {}]],
                            'tables': {
                                'annualTotalRevenue': {
                                    'column_settings': [
                                        ['all', ''],
                                    ],
                                },
                                'quarterlyTotalRevenue': {
                                    'column_settings': [
                                        ['all', ''],
                                    ],
                                },
                                'trailingTotalRevenue': {
                                    'column_settings': [
                                        ['all', ''],
                                    ],
                                },
                                'annualOperatingRevenue': {
                                    'column_settings': [
                                        ['all', ''],
                                    ],
                                },
                                'quarterlyOperatingRevenue': {
                                    'column_settings': [
                                        ['all', ''],
                                    ],
                                },
                                'trailingOperatingRevenue': {
                                    'column_settings': [
                                        ['all', ''],
                                    ],
                                },
                            },
                        },
                    },
                },
            },
        },
    }
