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
    def merge(self, data, allow_collision=False):
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
    
    catalog = {
        'symbols': {
            'info': 'get all symbols in our scrapes',
            # 'post_procs': [[merge, {}]],
            'sets': {
                'Yahoo_Quote': {
                    'post_procs': [[merge, {'allow_collision': True}]],
                    'scrapes': {
                        Yahoo_Quote: {
                            'all': {
                                'column_settings': [
                                    ['symbol', 'symbol'],
                                ],
                            },
                        },
                    },
                },
                'Yahoo_Chart': {
                    'post_procs': [[merge, {}]],
                    'scrapes': {
                        Yahoo_Chart: {
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
       'us_symbols': {
            'info': 'get all symbols for market and locale',
            # 'post_procs': [[merge, {}]],
            'sets': {
                'symbols': {
                    # 'post_procs': [[merge, {}]],
                    'scrapes': {
                        FMP_Stocklist: {
                            'stocklist': {
                                'column_settings': [
                                    ['exchangeShortName', 'acronym'],
                                ],
                            },
                        },
                        Polygon_Tickers: {
                            'tickers': {
                                'column_settings': [
                                    ['locale', 'locale'],
                                    ['market', 'market'],
                                ],
                            },
                        },
                    },
                },
                'iso': {
                    'post_procs': [[merge, {}]],
                    'scrapes': {
                        File_Files: {
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
        'update_nightly': {
            'info': 'update all scrapes',
            'sets': {
                'all': {
                    'scrapes': {
                        Yahoo_Quote: {'all': {},},
                        Yahoo_Chart: {'all': {},},
                        Finviz_Ticker_News: {'all': {},},
                        Polygon_News: {'all': {},},
                        File_Files: {'all': {},},
                    },
                },
            },
        },
        'update_all': {
            'info': 'update all scrapes',
            'sets': {
                'all': {
                    'scrapes': {
                        Yahoo_Quote: {'all': {},},
                        Yahoo_Chart: {'all': {},},
                        Finviz_Ticker_News: {'all': {},},
                        Polygon_News: {'all': {},},
                    },
                },
            },
        },
        'update_test': {
            'info': 'scrapes update test',
            'sets': {
                'all': {
                    'scrapes': {
                        Yahoo_Chart: {'all': {},},
                    },
                },
            },
        },
        'statistics': {
            'info': 'catalog test',
            'post_procs': [[merge, {}]],
            'sets': {
                'test': {
                    'post_procs': [[merge, {}]],
                    'scrapes': {
                        Yahoo_Quote: {
                            'defaultKeyStatistics': {
                                'column_settings': [
                                    ['trailingEps', 'trailingEps'],
                                    ['forwardEps', 'forwardEps'],
                                    ['forwardPE', 'forwardPE_a'],
                                    ['beta', 'beta'],
                                    ['beta3Year', 'beta3Year'],
                                    ['pegRatio', 'pegRatio'],
                                    ['yield', 'yield'],
                                    ['sharesOutstanding', 'sharesOutstanding'],
                                ],
                            },
                            'summaryDetail': {
                                'column_settings': [
                                    ['forwardPE', 'forwardPE_b'],
                                    ['trailingPE', 'trailingPE'],
                                    ['trailingAnnualDividendRate', 'ttmDividendRate'],
                                ],
                            },
                            'financialData': {
                                'column_settings': [
                                    ['earningsGrowth', 'earningsGrowth'],
                                    ['revenueGrowth', 'revenueGrowth'],
                                    ['revenuePerShare', 'revenuePerShare'],
                                ],
                            },
                            'earningsHistory': {
                                'column_settings': [
                                    ['history', 'history'],
                                ],
                            },
                        },
                    },
                },
                'test_b': {
                    'post_procs': [[merge, {}]],
                    'scrapes': {
                        Yahoo_Chart: {
                            'table_reference': {
                                'column_settings': [
                                    ['chart', 'ref_name'],
                                ],
                            },
                        },
                    },
                },
            },
        },
    }
