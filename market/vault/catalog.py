from ..scrape import *

class Catalog():
    def __init__(self):
        pass

    def get_catalog(self, catalog_name):
        if catalog_name in self.__catalog:
            return self.__catalog[catalog_name]
        return {}

    __catalog = {
        'test': {
            'info': 'ticker earnings',
            # 'postProcs': [[__dropParent, {}]],
            'sets': {
                # 'test_set_a': {
                #     # 'postProcs': [[__dropParent, {}]],
                #     'scrapes': {
                #         Yahoo_Quote: {
                #             'quoteType': {
                #                 'keyValues': True,
                #                 'columnSettings': [
                #                     ['all', '', {}],
                #                 ],
                #             },
                #         },
                #     },
                # },
                # 'test_set_b': {
                #     # 'postProcs': [[__dropParent, {}]],
                #     'scrapes': {
                #         Yahoo_Quote: {
                #             'defaultKeyStatistics': {
                #                 'keyValues': True,
                #                 'columnSettings': [
                #                     ['all', '', {}],
                #                 ],
                #             },
                #         },
                #     },
                # },
                # 'test_set_c': {
                #     # 'postProcs': [[__dropParent, {}]],
                #     'scrapes': {
                #         FMP_Stocklist: {
                #             'stocklist': {
                #                 'keyValues': True,
                #                 'columnSettings': [
                #                     ['all', '', {}],
                #                 ],
                #             },
                #         },
                #     },
                # },
                'test_set_d': {
                    # 'postProcs': [[__dropParent, {}]],
                    'scrapes': {
                        Polygon_Tickers: {
                            'tickers': {
                                'keyValues': True,
                                'columnSettings': [
                                    ['all', '', {}],
                                ],
                            },
                        },
                    },
                },
            },
        },
    }
