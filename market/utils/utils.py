import pandas as pd
import numpy as np

def get_average(df, median_threshold=0.1):
    average = pd.DataFrame()
    average['mean'] = df.mean()
    average['median'] = df.median()
    average = average.T
    average.loc['deviation'] = np.abs(average.diff().iloc[-1]) / np.abs(average).max()
    average = average.T
    average.loc[average['deviation'] > median_threshold, 'average'] = average['median']
    average.loc[average['deviation'] <= median_threshold, 'average'] = average['mean']
    return average['average']

def get_trends(df, ratio_base=None, fill_gaps=True):
    df = df.dropna(how='all', axis=0)
    trends = pd.DataFrame(columns=['trend', 'trend_ratio', 'trend_step', 'trend_step_ratio', 'volatility', 'step_count', 'last_valid_value', 'last_valid_index'])
    for column in df.columns:
        column_data = df[column]

        last_valid_index = column_data.last_valid_index()
        if last_valid_index is None:
            trends.loc[column, 'last_valid_index'] = np.nan
            trends.loc[column, 'last_valid_value'] = np.nan
        else:
            trends.loc[column, 'last_valid_index'] = last_valid_index
            trends.loc[column, 'last_valid_value'] = column_data.loc[last_valid_index]

        # got data from first notna to last notna 
        column_data = column_data.loc[column_data.first_valid_index():column_data.last_valid_index()]

        # we have no trending data
        if column_data.shape[0] < 2:
            trends.loc[column] = np.nan
            continue
        
        # linear interpolate data for missing gaps
        if fill_gaps:
            column_data = column_data.interpolate(method='linear')
        elif column_data.isna().any():
            trends.loc[column] = np.nan
            continue

        # reset index for linear regression
        column_data = column_data.reset_index(drop=True)

        trends.loc[column, 'step_count'] = column_data.shape[0]

        coeffs = np.polyfit(column_data.index, column_data.values, 1)
        trend = np.polyval(coeffs, column_data.index)
        trend_mean = np.abs(trend.mean())
        if trend_mean == 0:
            trends.loc[column] = np.nan
            continue
        
        # get trend values
        trends.loc[column, 'trend_step'] = coeffs[0]
        trends.loc[column, 'trend'] = coeffs[0] * column_data.shape[0]
        if ratio_base is not None:
            trends.loc[column, 'trend_step_ratio'] = coeffs[0] / np.abs(ratio_base)
            trends.loc[column, 'trend_ratio'] = (coeffs[0] / np.abs(ratio_base)) * column_data.shape[0]
        else:
            trends.loc[column, 'trend_step_ratio'] = coeffs[0] / trend_mean
            trends.loc[column, 'trend_ratio'] = (coeffs[0] / trend_mean) * column_data.shape[0]
        
        # calculate volatility
        residual_std = np.std(column_data.values - trend)
        trends.loc[column, 'volatility'] = residual_std / trend_mean
    
    return trends
