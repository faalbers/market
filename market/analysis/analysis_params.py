class Analysis_Params():
    def __init__(self):
        pass

    params = {
        'current_ratio': {
            'info':
"""Current Ratio is a financial metric used in company statements to assess a company's short-term liquidity,
or its ability to meet its short-term financial obligations with its current assets.
It's a key liquidity ratio found on a company's balance sheet.""",
            'unit': '%',
            'guidance': 'Should be 100 or up',
        },
        'cash_ratio': {
            'info':
"""Cash Ratio is a financial metric used in company statements to assess a company's immediate ability to meet
its short-term debt obligations using only its most liquid assets: cash and cash equivalents. 
This metric assesses if a company can meet its immediate debts using only cash and near-cash assets. 
If it's too high it does not take up enough liabilities for growth and is too conservative""",
            'unit': '%',
            'guidance': 'Should be between 50 and 100',
        },
        'gross_profit_margin': {
            'info':
"""Gross Profit Margin is a fundamental financial metric that gauges a company's profitability and operational efficiency.
It is the percentage of revenue that a company retains after subtracting the direct costs associated with producing or
delivering its goods or services, known as the Cost of Goods Sold (COGS).""",
            'unit': '%',
            'guidance': 'Should be 25 or up',
        },
        'net_profit_margin': {
            'info':
"""Net Profit Margin is a crucial financial ratio that indicates how much profit a company retains for each dollar of
revenue generated after accounting for all expenses, including operating costs, interest, and taxes. It's a key
indicator of a company's overall financial health and operational efficiency. A higher net profit margin generally
suggests that a company is managing its costs effectively and generating substantial profits from its operations.
Conversely, a lower margin may indicate financial struggles, weak pricing strategies, or inefficiencies.""",
            'unit': '%',
            'guidance': 'Should be 15 or up',
        },
        'operating_profit_margin': {
            'info':
"""Operating Profit Margin, also called operating profit margin or return on sales (ROS), is a financial ratio that measures
a company's profitability and operational efficiency. It indicates how much profit a company makes from its
core business operations after deducting the direct and indirect costs associated with those operations,
relative to its total revenue.""",
            'unit': '%',
            'guidance': 'Should be 25 or up',
        },
        'profit_margin': {
            'info':
"""Profit Margin, also called profit margin or return on earnings (ROE), is a crucial financial ratio that indicates how much
profit a company retains for each dollar of revenue generated after accounting for all expenses, including operating costs,
interest, taxes are NOT included. It's a key indicator of a company's overall financial health and operational efficiency.
A higher profit margin generally suggests that a company is managing its costs effectively and generating substantial profits
from its operations.
Conversely, a lower margin may indicate financial struggles, weak pricing strategies, or inefficiencies.""",
            'unit': '%',
            'guidance': 'Should be 20 or up',
        },
        'dividends': {
            'info':
"""A dividend is a distribution of a company's earnings to its shareholders. When a company earns a profit, its board of directors
may decide to pay a portion of that profit to its investors as a reward for their investment, rather than reinvesting it all back
into the business.
""",
            'unit': '%',
        },
        'sector': {
            'info':
"""A stock sector is a large grouping of companies that operate in the same part of the economy, sorted by their primary business
activities, such as healthcare, technology, energy, or financials. Investors categorize companies into sectors to understand
overall market trends and diversify their portfolios by spreading investments across different economic segments.
""",
            'values': [
                'Basic Materials',
                'Communication Services',
                'Consumer Cyclical',
                'Consumer Defensive',
                'Energy',
                'Financial Services',
                'Healthcare',
                'Industrials',
                'Real Estate',
                'Technology',
            ],
        },
        'industry': {
            'info':
"""The industry of a stock is its company's primary business activity, determined by where most of its revenue is generated,
which helps group stocks with similar operations and economic characteristics for portfolio diversification and analysis.
By classifying companies into industries and larger sectors, investors can understand how different parts of the economy are
performing and identify risks and opportunities.
""",
        },
        'type': {
            'info':
                "Type of a stock",
            'values': [
                'EQUITY',
                'ETF',
                'INDEX',
                'MONEYMARKET',
                'MUTUALFUND',
                'NONE',
            ],
        },
        'name': {
            'info':
                "Full name of a stock",
        },
        'market_cap': {
            'info':
"""The market capitalization, or market cap, of a stock is the total market value of a company's outstanding shares,
calculated by multiplying the current stock price by the number of shares outstanding. It's a key indicator of a
company's size, which can help investors understand its relative market standing, risk, and growth potential.
For example, a company with 10 million shares outstanding and a stock price of $35 would have a market cap of $350 million.
""",
            'values': [
                'Small (250M <-> 2B)',
                'Mid (2B <-> 10B)',
                'Large (10B <-> 200B)',
                'Mega (200B +)',
            ],
        },
        'minervini_score': {
            'info':
"""The Minervini score uses Mark Minervini's "Trend Template" criteria, focusing on stocks in strong uptrends by checking
if the 50-day moving average (MA) is above the 150-day MA, and the 150-day MA is above the 200-day MA. It also requires
the current stock price to be above the 150-day and 200-day MAs and for the price to be within 25% of its 52-week high.
In addition to these technical factors, successful screeners also incorporate fundamental and relative strength (RS) criteria. 
""",
            'unit': 'value between 0 and 100',
        },
        'sub_type': {
            'info':
"""Polygon.io provides stock type codes, such as CS for Common Stock, that you can retrieve through their Ticker Types API
endpoint. Unlike standard industry classification codes, Polygon.io's ticker types are used to filter and categorize assets
within their own system. 
""",
            'values': [
                'CS (Common Stock)',
                'PFD (Preferred Stock)',
                'WARRANT (Warrant)',
                'RIGHT (Rights)',
                # 'BOND (Corporate Bond)',
                'ETF (Exchange Traded Fund)',
                'ETN (Exchange Traded Note)',
                'ETV (Exchange Traded Vehicle)',
                'SP (Structured Product)',
                'ADRC (American Depository Receipt Common)',
                # 'ADRP (American Depository Receipt Preferred)',
                # 'ADRW (American Depository Receipt Warrants)',
                # 'ADRR (American Depository Receipt Rights)',
                'FUND (Fund)',
                # 'BASKET (Basket)',
                'UNIT (Unit)',
                # 'LT (Liquidating Trust)',
                'OS (Ordinary Shares)',
                'GDR (Global Depository Receipts)',
                'OTHER (Other Security Type)',
                'NYRS (New York Registry Shares)',
                # 'AGEN (Agency Bond)',
                # 'EQLK (Equity Linked Bond)',
                'ETS (Single-security ETF)',
                'IX (Index)',
            ],
        },
        'fund_category': {
            'info':
"""A fund category in mutual funds is a way to classify funds based on their investment strategy, types of assets held,
and investment objectives. Common categories include equity funds (investing in stocks), debt funds
(investing in fixed-income securities), and hybrid funds (a mix of both). These categories help investors understand a
fund's potential risks, returns, and how it aligns with their financial goals.  
""",
        },
        'fund_family': {
            'info':
"""A fund family is a collection of different mutual funds and other investment products, like ETFs, offered by a single
investment management company, such as Vanguard or Fidelity. These funds within the same family share administrative and
operational systems and are overseen by the same company, allowing investors to access a wide range of investment options
and often providing benefits like lower fees, fee-free fund exchanges, and consolidated reporting within a single platform.   
""",
        },
        'pe_ttm': {
            'info':
"""The trailing price-to-earnings (P/E) ratio is a valuation metric that measures a company's current stock price relative
to its actual earnings per share (EPS) over the past 12 months. So how much $ you pay for $1 earnings.
It's calculated by dividing the current stock price by the company's earnings per share (EPS) for the past 12 months.
It's als called valuation multiples, or how many years of earnings needed to get back price.
""",
            'unit': '$ value per $ earnings',
            'guidance':
"""A lower trailing P/E ratio might suggest a stock is undervalued, while a higher ratio could indicate overvaluation.
Compare with others in same industry and sector (peers).
""",
        },
        'pe_forward': {
            'info':
"""The forward P/E ratio, also known as the leading or prospective P/E ratio, is a stock valuation metric that offers a glimpse
into a company's future earnings potential. The forward P/E ratio estimates how much investors are willing to pay for each dollar
of a company's projected future earnings. Unlike the trailing P/E ratio, which uses past earnings data, the forward P/E is
forward-looking and relies on estimates of future earnings, which are typically provided by company management or financial analysts.
""",
            'unit': '$ value per $ earnings',
            'guidance': "Remember, it is soley based on predicted data. Compare with others in same industry and sector (peers).",
        },
        'peg_ttm': {
            'info':
"""A trailing PEG ratio is a stock valuation metric that divides a company's trailing P/E ratio (the price-to-earnings ratio
based on the past 12 months of actual earnings) by a historical earnings growth rate, which could be from the last fiscal year
or a multi-year average. It indicates if a stock's current price is justified by its past earnings performance and growth. 
""",
            'unit': 'around 1.0',
            'guidance': [
                'Compare with others in same industry and sector.',
                'PEG ttm = 1:',
                '    Suggests the stock is fairly valued, where the market price aligns with historical earnings growth',
                'PEG ttm < 1:',
                '    May indicate the stock is undervalued, offering potential growth at a reasonable price',
                'PEG ttm > 1:',
                '    Could indicate the stock is overvalued relative to its historical growth, signaling caution.',
            ]
        },
        'margin_of_safety': {
            'info':
"""The margin of safety refers to the difference between a stock's intrinsic value (what it's worth in 10 years based on fundamentals)
and its market cap (what it's currently worth)""",
            'unit': '%',
            'guidance': 'Buy above a certain value. Most select 35%. Lower value is more risk.',
        },
    }
    
    def get_param_info(self, param):
        info = {}

        # find param
        param_found = None
        for param_search in self.params:
            if param.startswith(param_search):
                param_found = param_search
                break
        if param_found is None:
            return info
        
        info['name'] = param
        info['base_name'] = param_found.replace('_', ' ').title()
        info['info'] = self.params[param_found]['info']
        if 'unit' in self.params[param_found]: info['unit'] = self.params[param_found]['unit']
        if 'values' in self.params[param_found]: info['values'] = self.params[param_found]['values']
        if 'guidance' in self.params[param_found]: info['guidance'] = self.params[param_found]['guidance']

        # get suffixes
        param = param.replace(param_found, '')
        info['suffix'] = param

        if 'yearly' in param:
            info['periods'] = 'yearly'
            if 'trend' in param:
                info['periodic'] = \
                f"This is a yearly trend amount over '{param_found}_yearly_count' years "+ \
                f"and ending in the year '{param_found}_yearly_end_year'"
            elif 'volatility' in param:
                info['periodic'] = \
                f"This is the volatility percentage from the period over '{param_found}_yearly_count' years "+ \
                f"and ending in the year '{param_found}_yearly_end_year'"
            elif 'count' in param:
                info['periodic'] = \
                f"This is the amount of years the periodic data was assessed over"
            elif 'end_year' in param:
                info['periodic'] = \
                f"This is the end year the periodic data was assessed over"
            else:
                info['periodic'] = \
                f"This is the amount ending in the year '{param_found}_yearly_end_year'"
        
        elif 'ttm' in param:
            info['periods'] = 'ttm'
            if 'trend' in param:
                info['periodic'] = \
                f"This is a 12 months block period trend amount over the count of '{param_found}_ttm_count' periods "+ \
                f"and ending in the last block period"
            elif 'volatility' in param:
                info['periodic'] = \
                f"This is the volatility percentage from last 12 months block period amount over the count of '{param_found}_ttm_count' periods "+ \
                f"and ending in the last block period"
            elif 'count' in param:
                info['periodic'] = \
                f"This is the amount of 12 months block periods the periodic data was assessed over"
            else:
                info['periodic'] = \
                f"This is the amount in the last 12 months block period"
        
        elif 'quarterly' in param:
            info['periods'] = 'quarterly'
            if 'trend' in param:
                info['periodic'] = \
                f"This is a quarterly trend amount over the count of '{param_found}_quarterly_count' quarters "+ \
                f"and ending in the quarter year '{param_found}_quarterly_end_year' and month '{param_found}_quarterly_end_month'"
            elif 'volatility' in param:
                info['periodic'] = \
                f"This is the volatility percentage from the periods over '{param_found}_quarterly_count' quarters "+ \
                f"and ending in the quarter year '{param_found}_quarterly_end_year' and month '{param_found}_quarterly_end_month'"
            elif 'count' in param:
                info['periodic'] = \
                f"This is the amount of quarters the periodic data was assessed over"
            elif 'end_year' in param:
                info['periodic'] = \
                f"This is the end year the periodic data was assessed over"
            elif 'end_month' in param:
                info['periodic'] = \
                f"This is the end month the periodic data was assessed over"
            else:
                info['periodic'] = \
                f"This is the amount ending in the quarter '{param_found}_quarterly_end_year' and month '{param_found}_quarterly_end_month'"

        elif 'peers_diff' in param:
            if 'ratio' in param:
                info['peers_diff'] = \
                f"This is the ratio of the difference between the value of '{param_found}' and the average of all of it's peers."
            else:
                info['peers_diff'] = \
                f"This is the difference between the value of '{param_found}' and the average of all of it's peers."
        
        elif 'volatility' in param:
            info['volatility'] = \
            f"This is the volatility percentage from periods used to calculate this value."
        
        return info
