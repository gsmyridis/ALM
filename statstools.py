import pandas as pd
from statsmodels.tsa.stattools import adfuller, kpss

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