from ..scrape import *

class Catalog():
    def __init__(self):
        pass

    catalog = {
        'update_data': {
            FMP_Stocklist: {'stocklist': [],},
            Polygon_Tickers: {'tickers': []},
            Fred: {'fred': []},
            File_Files: {'mic': [], 'country': [],},
            Polygon_News: {'news_polygon': [],},
        },
        'update_symbols_all': {
            YahooF_Info: {'info': [],},
        },
        'update_symbols_info': {
            Finviz_Ticker_News: {'news_finviz': [],},
            Etrade_Quote: {'quote': [],},
            YahooF_Chart: {'chart': [],},
        },
        'update_symbols_equity': {
            YahooF_Fundamental: {'fundamental': [],},
        },
        'profile': {
            YahooF_Info: {
                'info': [
                    ['longName', 'name'],
                    ['quoteType', 'type'],
                ],
            },
        },
        'chart': {
            YahooF_Chart: {
                # getting all columns to speed it up
                'chart': [],
            },
        },
        'fundamental': {
            YahooF_Fundamental: {
                'trailing': [
                    ['OperatingIncome', 'operating_income'],
                ],
                'yearly': [
                    ['OperatingIncome', 'operating_income'],
                ],
                'quarterly': [
                    ['OperatingIncome', 'operating_income'],
                ],
            },
        },
        'news': {
            # Finviz_Ticker_News: {
            #     'news_finviz': [
            #         ['Title', 'title'],
            #         ['sentiment_llama', 'sentiment'],
            #     ],
            # },
            Polygon_News: {
                'news_polygon': [
                    ['title', 'title'],
                    # ['sentiment_llama', 'sentiment'],
                ],
            },
        },
        'symbols': {
            FMP_Stocklist: {
                'stocklist': [
                    ['name', 'name'],
                    ['type', 'type'],
                    # ['exchangeShortName', 'exchange'],
                ]},
            Polygon_Tickers: {
                'tickers': [
                    ['name', 'name_tickers'],
                    ['type', 'sub_type'],
                    # ['primary_exchange', 'exchange'],
                    ['market', 'market'],
                ]},
            YahooF_Info: {
                'info': [
                    ['shortName', 'name_short'],
                    ['quoteType', 'type'],
                ],
            },
        },
        'us_symbols': {
            FMP_Stocklist: {
                'stocklist': [
                    ['exchangeShortName', 'acronym'],
                ],
            },
            Polygon_Tickers: {
                'tickers': [
                    ['locale', 'locale'],
                    ['market', 'market'],
                ],
            },
            File_Files: {
                'mic': [
                    ['ACRONYM', 'acronym'],
                    ['ISO COUNTRY CODE (ISO 3166)', 'cc'],
                ],
            },
        },
        'analysis': {
            YahooF_Info: {
                'info': [
                    ['longName', 'name'],
                    ['longBusinessSummary', 'info'],
                    ['quoteType', 'type'],
                    ['exchange', 'exchange'],
                    ['fullExchangeName', 'exchange_name'],
                    ['exchangeTimezoneShortName', 'exchange_time_zone'],
                    ['exchangeTimezoneName', 'exchange_time_zone_name'],
                    ['fundFamily', 'etf_family'],
                    ['sectorDisp', 'sector'],
                    ['industryDisp', 'industry'],
                    ['category', 'etf_category'],
                    ['epsCurrentYear', 'earnings_per_share_current_year'],
                    ['epsTrailingTwelveMonths', 'earnings_per_share_trailing'],
                    ['epsForward', 'earnings_per_share_forward'],
                    ['revenuePerShare', 'revenue_per_share'],
                    ['revenueGrowth', 'revenue_growth'],
                    ['earningsGrowth', 'earnings_growth'],
                    ['earningsQuarterlyGrowth', 'earnings_growth_quarterly'],
                    ['trailingPE', 'price_to_earnings_trailing'],
                    ['forwardPE', 'price_to_earnings_forward'],
                    ['trailingPegRatio', 'price_to_earnings_to_growth_trailing'],
                    ['lastDividendValue', 'dividend_last'],
                    ['dividendYield', 'dividend_yield'],
                    ['trailingAnnualDividendYield', 'dividend_yield_trailing'],
                    ['dividendRate', 'dividend_rate'],
                    ['trailingAnnualDividendRate', 'dividend_rate_trailing'],
                    ['dividendDate', 'dividend_date_execution'],
                    ['exDividendDate', 'dividend_date_record'],
                    ['lastDividendDate', 'dividend_date_record_last'],
                    ['regularMarketPrice', 'price'],
                    ['bookValue', 'book_value_per_share'],
                    ['netExpenseRatio', 'expense_ratio'],
                    ['fund_data', 'fund_data'],
                    ['recommendations', 'recommendations'],
                    ['growth_estimates', 'growth_estimates'],
                    ['eps_trend', 'earnings_per_share_trend'],
                    ['upgrades_downgrades', 'upgrades_downgrades'],
                ],
            },
            YahooF_Fundamental: {
                'fundamental': [
                    ['Share Issued', 'shares_out'],
                    ['Total Debt', 'total_debt'],
                ],
            },
            Etrade_Quote: {
                'quote': [
                    ['symbol', 'etrade_symbol'],
                    ['availability', 'etrade_availability_info'],
                    ['initialInvestment', 'initial_investment'],
                    ['transactionFee', 'transaction_fee'],
                    ['earlyRedemptionFee', 'early_redemption_fee'],
                    ['etradeEarlyRedemptionFee', 'early_redemption_fee_etrade'],
                ],
            },
            YahooF_Chart: {
                'chart': [
                    ['Close', 'close'],
                    ['Adj Close', 'adjusted_close'],
                    ['Dividends', 'dividends'],
                    ['Capital Gains', 'capital_gains'],
                    ['Stock Splits', 'splits'],
                ],
            },
        },
    }
