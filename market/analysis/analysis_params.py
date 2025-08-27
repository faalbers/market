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
        },
        'cash_ratio': {
            'info':
"""Cash Ratio is a financial metric used in company statements to assess a company's immediate ability to meet
its short-term debt obligations using only its most liquid assets: cash and cash equivalents. 
This metric assesses if a company can meet its immediate debts using only cash and near-cash assets. 
If it's too high it does not take up enough liabilities for growth and is too conservative""",
            'unit': '%',
        },
        'gross_profit_margin': {
            'info':
"""Gross Profit Margin is a fundamental financial metric that gauges a company's profitability and operational efficiency.
It is the percentage of revenue that a company retains after subtracting the direct costs associated with producing or
delivering its goods or services, known as the Cost of Goods Sold (COGS).""",
            'unit': '%',
        },
        'net_profit_margin': {
            'info':
"""Net Profit Margin is a crucial financial ratio that indicates how much profit a company retains for each dollar of
revenue generated after accounting for all expenses, including operating costs, interest, and taxes. It's a key
indicator of a company's overall financial health and operational efficiency. A higher net profit margin generally
suggests that a company is managing its costs effectively and generating substantial profits from its operations.
Conversely, a lower margin may indicate financial struggles, weak pricing strategies, or inefficiencies.""",
            'unit': '%',
        },
        'operating_profit_margin': {
            'info':
"""Operating Profit Margin, also called operating profit margin or return on sales (ROS), is a financial ratio that measures
a company's profitability and operational efficiency. It indicates how much profit a company makes from its
core business operations after deducting the direct and indirect costs associated with those operations,
relative to its total revenue.""",
            'unit': '%',
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
        },
        'dividends': {
            'info':
"""Dividends are dividends""",
            'unit': '%',
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
        info['unit'] = self.params[param_found]['unit']
        info['info'] = self.params[param_found]['info']

        # get suffixes
        param = param.replace(param_found, '')

        if 'yearly' in param:
            if 'trend' in param:
                info['periodic'] = \
                f"This is a yearly trend amount over '{param_found}_yearly_count' years "+ \
                f"and ending in the year '{param_found}_yearly_end_year'"
            elif 'std_%' in param:
                info['periodic'] = \
                f"This is a standard deviation percentage from last year's amount over '{param_found}_yearly_count' years "+ \
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
            if 'trend' in param:
                info['periodic'] = \
                f"This is a 12 months block period trend amount over the count of '{param_found}_ttm_count' periods "+ \
                f"and ending in the last block period"
            elif 'std_%' in param:
                info['periodic'] = \
                f"This is a standard deviation percentage from last 12 months block period amount over the count of '{param_found}_ttm_count' periods "+ \
                f"and ending in the last block period"
            elif 'count' in param:
                info['periodic'] = \
                f"This is the amount of 12 months block periods the periodic data was assessed over"
            else:
                info['periodic'] = \
                f"This is the amount in the last 12 months block period"
        
        elif 'quarterly' in param:
            if 'trend' in param:
                info['periodic'] = \
                f"This is a quarterly trend amount over the count of '{param_found}_quarterly_count' quarters "+ \
                f"and ending in the quarter year '{param_found}_quarterly_end_year' and month '{param_found}_quarterly_end_month'"
            elif 'std_%' in param:
                info['periodic'] = \
                f"This is a standard deviation percentage from last quarter's amount over the of '{param_found}_quarterly_count' quarters "+ \
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
        
        return info
