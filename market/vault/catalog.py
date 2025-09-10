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
                    # ['longBusinessSummary', 'description'],
                    ['fullExchangeName', 'exchange_name'],
                    ['sectorDisp', 'sector'],
                    ['industryDisp', 'industry'],
                    ['marketCap', 'market_cap'],
                    ['currentPrice', 'price'],
                    ['trailingPE', 'pe_trailing'],
                    # ['category', 'etf_category'],
                    # ['fundFamily', 'etf_family'],
                ],
            },
        },
        'chart': {
            YahooF_Chart: {
                'chart': [
                    ['Adj Close', 'price'],
                    ['High', 'high'],
                    ['Low', 'low'],
                    ['Volume', 'volume'],
                    ['Dividends', 'dividends'],
                    ['Stock Splits', 'stock_splits'],
                    ['Capital Gains', 'capital_gains'],
                ],
            },
        },
        'fundamental': {
            YahooF_Fundamental: {
                'trailing': [
                    ['CurrentAssets', 'current_assets'],
                    ['CurrentLiabilities', 'current_liabilities'],
                    ['CashAndCashEquivalents', 'cash_and_cash_equivalents'],
                    ['FreeCashFlow', 'free_cash_flow'],
                    ['TotalRevenue', 'total_revenue'],
                    ['GrossProfit', 'gross_profit'],
                    ['OperatingIncome', 'operating_income'],
                    ['PretaxIncome', 'pretax_income'],
                    ['NetIncome', 'net_income'],
                    ['DilutedEPS', 'eps'],
                ],
                'yearly': [
                    ['CurrentAssets', 'current_assets'],
                    ['CurrentLiabilities', 'current_liabilities'],
                    ['CashAndCashEquivalents', 'cash_and_cash_equivalents'],
                    ['FreeCashFlow', 'free_cash_flow'],
                    ['TotalRevenue', 'total_revenue'],
                    ['GrossProfit', 'gross_profit'],
                    ['OperatingIncome', 'operating_income'],
                    ['PretaxIncome', 'pretax_income'],
                    ['NetIncome', 'net_income'],
                    ['DilutedEPS', 'eps'],
                ],
                'quarterly': [
                    ['CurrentAssets', 'current_assets'],
                    ['CurrentLiabilities', 'current_liabilities'],
                    ['CashAndCashEquivalents', 'cash_and_cash_equivalents'],
                    ['FreeCashFlow', 'free_cash_flow'],
                    ['TotalRevenue', 'total_revenue'],
                    ['GrossProfit', 'gross_profit'],
                    ['OperatingIncome', 'operating_income'],
                    ['PretaxIncome', 'pretax_income'],
                    ['NetIncome', 'net_income'],
                    ['DilutedEPS', 'eps'],
                ],
            },
            YahooF_Chart: {
                'chart': [
                    ['Adj Close', 'price'],
                ],
            },
        },
        'news': {
            Finviz_Ticker_News: {
                'news_finviz': [
                    ['Title', 'title'],
                    ['Link', 'url'],
                    # ['sentiment_llama', 'sentiment'],
                ],
            },
            Polygon_News: {
                'news_polygon': [
                    ['title', 'title'],
                    ['article_url', 'url'],
                    # ['description', 'description'],
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
        'info': {
            YahooF_Info: {
                'info': [],
                # 'upgrades_downgrades': [],
            },
        },
        'analysis': {
            YahooF_Info: {
                'info': [
                    ['sectorDisp', 'sector'],
                    ['industryDisp', 'industry'],
                    
                    ['marketCap', 'market_cap'],
                    ['trailingPE', 'pe_ttm'],
                    ['forwardPE', 'pe_forward'],
                    ['trailingPegRatio', 'peg_ttm'],
                    ['fundOverview', 'fund_overview'],
                    # ['sharesOutstanding', 'shares'],
                    # ['currentPrice', 'price'],
                    
                    # ['trailingEps', 'eps_ttm'],
                    
                    # ['priceToSalesTrailing12Months', 'ps_ttm'],

                    # ['growthEstimates', 'growth_estimates'],

                    
                    
                    # ['dividendRate', 'dividend_rate_forward_$'],
                    # ['trailingAnnualDividendRate', 'dividend_rate_ttm_$'],

                    # ['dividendYield', 'dividend_yield_forward_%'],
                    # ['fiveYearAvgDividendYield', 'dividend_yield_5y_average_%'],
                    # ['trailingAnnualDividendYield', 'dividend_yield_ttm_%'],
                    

                    # ['fullExchangeName', 'exchange_name'],
                    # ['timestamp', 'data_time'],
                    # ['epsCurrentYear', 'eps_current_year'],
                    # ['epsTrailingTwelveMonths', 'eps_ttm'],
                    # ['epsForward', 'eps_forward'],

                    # ['revenuePerShare', 'revenue_per_share'],
                    # ['revenueGrowth', 'revenue_growth'],

                    # ['earningsGrowth', 'earnings_growth'],
                    # ['earningsQuarterlyGrowth', 'earnings_growth_quarterly'],

                    # ['trailingPE', 'pe_ttm'],
                    # ['forwardPE', 'pe_forward'],

                    # ['trailingPegRatio', 'peg_ttm'],

                    # ['lastDividendValue', 'dividend_last'],
                    # ['dividendYield', 'dividend_yield'],
                    # ['trailingAnnualDividendYield', 'dividend_yield_ttm'],
                    # ['dividendRate', 'dividend_rate'],
                    # ['trailingAnnualDividendRate', 'dividend_rate_ttm'],
                    # ['dividendDate', 'dividend_date_execution'],
                    # ['exDividendDate', 'dividend_date_record'],
                    # ['lastDividendDate', 'dividend_date_record_last'],

                    # ['bookValue', 'book_value_per_share'],
                    
                    # ['netExpenseRatio', 'expense_ratio'],
                    
                    # ['fund_data', 'fund_data'],
                    
                    # ['recommendations', 'recommendations'],
                    # ['growth_estimates', 'growth_estimates'],
                    # ['eps_trend', 'earnings_per_share_trend'],
                    # ['upgrades_downgrades', 'upgrades_downgrades'],

                ],
            },
            YahooF_Fundamental: {
                'trailing': [
                    ['CurrentAssets', 'current_assets'],
                    ['CurrentLiabilities', 'current_liabilities'],
                    ['CashAndCashEquivalents', 'cash_and_cash_equivalents'],
                    ['FreeCashFlow', 'free_cash_flow'],
                    ['TotalRevenue', 'total_revenue'],
                    ['GrossProfit', 'gross_profit'],
                    ['OperatingIncome', 'operating_income'],
                    ['PretaxIncome', 'pretax_income'],
                    ['NetIncome', 'net_income'],
                    ['DilutedEPS', 'eps'],
                    ['DilutedAverageShares', 'shares'],
                ],
                'yearly': [
                    ['CurrentAssets', 'current_assets'],
                    ['CurrentLiabilities', 'current_liabilities'],
                    ['CashAndCashEquivalents', 'cash_and_cash_equivalents'],
                    ['FreeCashFlow', 'free_cash_flow'],
                    ['TotalRevenue', 'total_revenue'],
                    ['GrossProfit', 'gross_profit'],
                    ['OperatingIncome', 'operating_income'],
                    ['PretaxIncome', 'pretax_income'],
                    ['NetIncome', 'net_income'],
                    ['DilutedEPS', 'eps'],
                    ['DilutedAverageShares', 'shares'],
                ],
                'quarterly': [
                    ['CurrentAssets', 'current_assets'],
                    ['CurrentLiabilities', 'current_liabilities'],
                    ['CashAndCashEquivalents', 'cash_and_cash_equivalents'],
                    ['FreeCashFlow', 'free_cash_flow'],
                    ['TotalRevenue', 'total_revenue'],
                    ['GrossProfit', 'gross_profit'],
                    ['OperatingIncome', 'operating_income'],
                    ['PretaxIncome', 'pretax_income'],
                    ['NetIncome', 'net_income'],
                    ['DilutedEPS', 'eps'],
                    ['DilutedAverageShares', 'shares'],
                ],
            },
            # Etrade_Quote: {
            #     'quote': [
            #         ['symbol', 'etrade_symbol'],
            #         ['availability', 'etrade_availability_info'],
            #         ['initialInvestment', 'initial_investment'],
            #         ['transactionFee', 'transaction_fee'],
            #         ['earlyRedemptionFee', 'early_redemption_fee'],
            #         ['etradeEarlyRedemptionFee', 'early_redemption_fee_etrade'],
            #     ],
            # },
            YahooF_Chart: {
                'chart': [
                    ['Adj Close', 'price'],
                    ['High', 'high'],
                    ['Low', 'low'],
                    ['Volume', 'volume'],
                    ['Dividends', 'dividends'],
                    ['Stock Splits', 'stock_splits'],
                    ['Capital Gains', 'capital_gains'],
                ],
            },
        },
    }
