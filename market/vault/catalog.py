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
    def merge(self, data):
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
                    else:
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
            'info': 'get all symbols for market and locale',
            # 'post_procs': [[merge, {}]],
            'sets': {
                'symbols': {
                    # 'post_procs': [[merge, {}]],
                    'scrapes': {
                        FMP_Stocklist: {
                            'stocklist': {
                                # 'key_values': True,
                                'column_settings': [
                                    ['exchangeShortName', 'acronym'],
                                ],
                            },
                        },
                        Polygon_Tickers: {
                            'tickers': {
                                # 'key_values': True,
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
                                # 'key_values': False,
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
        'update_all': {
            'info': 'update all scrapes',
            'sets': {
                'all': {
                    'scrapes': {
                        # Yahoo_Quote: {'all': {},},
                        # Yahoo_Chart: {'all': {},},
                        # Finviz_Ticker_News: {'all': {},},
                        Polygon_News: {'all': {},},
                    },
                },
            },
        },
        'update_us_symbols': {
            'info': 'update all scrapes that have symbols data to download',
            'sets': {
                'all': {
                    'scrapes': {
                        Yahoo_Quote: {'all': {},},
                        Yahoo_Chart: {'all': {},},
                        Finviz_Ticker_News: {'all': {},},
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
                                'key_values': True,
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
                                'key_values': True,
                                'column_settings': [
                                    ['forwardPE', 'forwardPE_b'],
                                    ['trailingPE', 'trailingPE'],
                                    ['trailingAnnualDividendRate', 'ttmDividendRate'],
                                ],
                            },
                            'financialData': {
                                'key_values': True,
                                'column_settings': [
                                    ['earningsGrowth', 'earningsGrowth'],
                                    ['revenueGrowth', 'revenueGrowth'],
                                    ['revenuePerShare', 'revenuePerShare'],
                                ],
                            },
                            'earningsHistory': {
                                'key_values': True,
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
                                'key_values': True,
                                'column_settings': [
                                    ['chart', 'ref_name'],
                                ],
                            },
                        },
                    },
                },
            },
        },
        # 'test': {
        #     'info': 'ticker earnings',
        #     # 'post_procs': [[__dropParent]],
        #     'sets': {
        #         # 'test_set_a': {
        #         #     # 'post_procs': [[__dropParent]],
        #         #     'scrapes': {
        #         #         Yahoo_Quote: {
        #         #             'all': {
        #         #                 'key_values': True,
        #         #                 'column_settings': [
        #         #                     ['all', ''],
        #         #                 ],
        #         #             },
        #         #         },
        #         #     },
        #         # },
        #         # 'test_set_c': {
        #         #     # 'post_procs': [[__dropParent]],
        #         #     'scrapes': {
        #         #         FMP_Stocklist: {
        #         #             'stocklist': {
        #         #                 'key_values': True,
        #         #                 'column_settings': [
        #         #                     ['all', ''],
        #         #                 ],
        #         #             },
        #         #         },
        #         #     },
        #         # },
        #         # 'test_set_d': {
        #         #     # 'post_procs': [[__dropParent]],
        #         #     'scrapes': {
        #         #         Polygon_Tickers: {
        #         #             'tickers': {
        #         #                 'key_values': True,
        #         #                 'column_settings': [
        #         #                     ['all', ''],
        #         #                 ],
        #         #             },
        #         #         },
        #         #     },
        #         # },
        #         # 'test_set_e': {
        #         #     # 'post_procs': [[__dropParent]],
        #         #     'scrapes': {
        #         #         File_Files: {
        #         #             'all': {
        #         #                 'key_values': False,
        #         #                 'column_settings': [
        #         #                     ['all', ''],
        #         #                 ],
        #         #             },
        #         #         },
        #         #     },
        #         # },
        #         # 'test_set_f': {
        #         #     # 'post_procs': [[__dropParent]],
        #         #     'scrapes': {
        #         #         Finviz_Ticker_News: {
        #         #             'table_reference': {
        #         #                 'key_values': True,
        #         #                 'column_settings': [
        #         #                     ['all', ''],
        #         #                 ],
        #         #             },
        #         #         },
        #         #     },
        #         # },
        #         # 'test_set_g': {
        #         #     # 'post_procs': [
        #         #     #     [
        #         #     #         get_reference,
        #         #     #         {
        #         #     #             'scrapeClass': Yahoo_Chart,
        #         #     #             'method': {
        #         #     #             },
        #         #     #         }
        #         #     #     ],
        #         #     # ],
        #         #     'scrapes': {
        #         #         Yahoo_Chart: {
        #         #             'table_reference': {
        #         #                 'key_values': True,
        #         #                 'column_settings': [
        #         #                     ['all', ''],
        #         #                 ],
        #         #             },
        #         #         },
        #         #     },
        #         # },
        #         # 'test_set_h': {
        #         #     # 'post_procs': [
        #         #     #     [
        #         #     #         get_reference,
        #         #     #         {
        #         #     #             'scrapeClass': Yahoo_Chart,
        #         #     #             'method': {
        #         #     #             },
        #         #     #         }
        #         #     #     ],
        #         #     # ],
        #         #     'scrapes': {
        #         #         Polygon_News: {
        #         #             'table_reference': {
        #         #                 'key_values': True,
        #         #                 'column_settings': [
        #         #                     ['all', ''],
        #         #                 ],
        #         #             },
        #         #         },
        #         #     },
        #         # },
        #     },
        # },
    }
