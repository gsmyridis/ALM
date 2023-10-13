import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from statsmodels.tsa.stattools import adfuller, kpss
from scipy.optimize import minimize

def adf_test(timeseries, verbose=False):
    """ Returns the results for the Augmented Dickey-Fuller Test """
    if verbose:
        print('Results of Dieke-Fuller Test:')
    dftest = adfuller(timeseries, autolag='AIC')
    dfoutput = pd.Series(dftest[0:4], index=['Test Statistic','p-value','#Lags Used','Number of Observations Used'])
    for key, value in dftest[4].items():
        dfoutput[f'Critical Value ({key})'] = value

    return dfoutput

def kpss_test(timeseries, verbose=False):
    """ Returns the resutls for the Kwiatkowski-Phillips-Schmidt-Shin Test """
    if verbose:
        print('Results of KPSS Test:')
    kpss_test = kpss(timeseries, regression='c', nlags='auto')
    kpss_output = pd.Series(kpss_test[0:3], index=['Test Statistic','p-value','Lags Used'])
    for key, value in kpss_test[3].items():
        kpss_output[f'Critical Value ({key})'] = value
    return kpss_output

def determine_order_of_integration(series, max_diff=3):
    """ Determines the order of integration for a given time series """
    d = 0  # initial order of integration
    while d <= max_diff:
        # If d is 0, we test the series itself
        if d == 0:
            test_series = series
        # Otherwise, we difference the series
        else:
            test_series = series.diff(periods=d).dropna()
        # Perform ADF test
        p_value = adf_test(test_series)['p-value']
        print(d, p_value)
        # If p-value is less than 0.05, we consider the series stationary
        if p_value < 0.05:
            return d
        else:
            d += 1
            
    return None  # None indicates that the series is not stationary even after max_diff differences

def replicate_portfolio(yields, coupons, objective_function='quadratic',
                        mean_maturity=60, initial_weights=None, plot=False):
    """  """
    # Make copies of the input dataframes
    yields_cp = yields.copy()
    coupons_cp = coupons.copy()

    # Keep the common dates of yields and coupons only
    dates = yields_cp.merge(coupons, on='date', how='inner')['date']
    ylds = yields_cp[yields['date'].isin(dates)]
    cpns = coupons_cp[coupons['date'].isin(dates)]

    # Plot the yields and coupons for common dates
    if plot:
        fig, ax = plt.subplots(2,1, figsize=(10, 6))
        for col in ylds.columns.drop('date'):
            ax[0].plot(ylds['date'], ylds[col], label=col)
        ax[0].plot(cpns['date'], cpns['cpn'], label='Coupon')
        ax[0].set_xlabel('Date')
        ax[0].set_ylabel('Yield')
        ax[0].legend()
        ax[0].set_title('Yields and Coupons')

    # Turn yields and coupons into numpy arrays
    ylds_np = ylds.drop(columns='date').to_numpy()
    cpns_np = cpns.drop(columns='date').to_numpy()

    # Months to maturity
    maturities = np.array([1, 3, 12, 60, 120])
    yields_num = len(maturities)
    
    # Define the quadratic objective function
    def objective_func(weights, A, b):
        if objective_function == 'quadratic':
            return np.linalg.norm(np.dot(A, weights) - b)
    
    # Constraints
    constraints = [{"type": "eq", "fun": lambda weights: np.sum(weights) - 1},
                   {"type": "eq", "fun": lambda weights: np.dot(maturities, weights) - mean_maturity}]
    # Boundaries for weights (0,1)
    bounds = [(0, 1) for _ in range(yields_num)]

    # Initial weights
    if initial_weights is None:
        initial_weights = np.ones(yields_num) / yields_num

    # Solve the optimization problem
    result = minimize(objective_func, initial_weights, args=(ylds_np, cpns_np), bounds=bounds, constraints=constraints)
    print(result)
    weights = pd.DataFrame(result.x, index = yields.columns.drop('date'), columns=['weight'])
 
    return weights