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
        for merge_name in list(data.keys()):
            # print(merge_name)
            for key_name, key_data in data.pop(merge_name).items(): 
                if not key_name in data:
                    data[key_name] = key_data
                else:
                    key_name_collision = set(data[key_name].keys()).intersection(key_data.keys())
                    if len(key_name_collision) > 0:
                        raise ValueError('Catalog.merge: key names collision: %s' % key_name_collision)
                    data[key_name] = {**data[key_name], **key_data}
    
    catalog = {
        'symbols': {
            'info': 'catalog test',
            # 'post_procs': [[merge, {}]],
            'sets': {
                'test': {
                    # 'post_procs': [[merge, {}]],
                    'scrapes': {
                        FMP_Stocklist: {
                            'stocklist': {
                                'key_values': True,
                                'column_settings': [
                                    ['exchangeShortName', 'acronym'],
                                ],
                            },
                        },
                        Polygon_Tickers: {
                            'tickers': {
                                'keyValues': True,
                                'columnSettings': [
                                    ['primary_exchange', 'mic'],
                                ],
                            },
                        },
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
