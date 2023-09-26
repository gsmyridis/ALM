import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

import utils
from nelson_siegel_svensson.calibrate import calibrate_nss_ols



class YieldCurve:
    
    def __init__(self, curve_type, today):
        """ Initialize parameters """
        self.curve_type = curve_type
        self._data = None
        self._curve = None
        self._status = None
        self._today = today
        
        
    def fit(self, market_data, plot=False):
        """ Fit Nelson-Siegel-Svensson model to the observed yields on the market """
        self._data = market_data[market_data['type'] == self.curve_type].copy()
        # Calculate time difference in years between now and expiry
        self._data['maturity'] = self._data['date'].apply(lambda date: utils.time_difference_years(date, self._today))
        # Fit the Nelson-Siegel-Svensson model to our yield data
        self._curve, self._status = calibrate_nss_ols(np.ravel(self._data['maturity']), np.ravel(self._data['rate']))

        if plot:
            self._plot_spot_yields(self._data['maturity'], self._data['rate'])
        
        
    def get_spot_yields(self, dates, plot=False):
        """ Gets the spot yield for dates based on Nelson-Siegel-Svensson model """
        maturities = utils.time_difference_years_from_list(dates, self._today)
        yields = self._curve(maturities)
        if plot:
            self._plot_spot_yields(dates, yields)
        return pd.DataFrame({"date": dates, "rate": yields})
         
        
    def _plot_spot_yields(self, times, rates):
        """ Plots the yields and the Nelson-Siegel-Svensson model vs dates of maturity """ 
        if isinstance(times[0], datetime):
            times_type = 'dates'
            times_scale = ''
            continuous_dates = utils.date_range(np.min(times), np.max(times), 100)
            continuous_maturities = utils.time_difference_years_from_list(continuous_dates, self._today)
            continuous_times = continuous_dates
        elif isinstance(times[0], float):
            times_type = 'times'
            times_scale = ' in years'
            continuous_maturities = np.linspace(np.min(times), np.max(times), 100)
            continuous_times = continuous_maturities
        else:
            raise TypeError('times can be either iterables of datetime.datetime or float numbers')
        
        plt.scatter(times, rates,
                    label='Spot Yields', marker='o', color='black', s=10)
        plt.plot(continuous_times, self._curve(continuous_maturities),
                 label='Nelson-Siegel-Svensson', color='gray', linestyle='-')
        
        plt.title(f'Yield Curve vs Maturity {times_type.capitalize()}')
        plt.xlabel(f'Maturity {times_type}' + times_scale)
        plt.ylabel('Yield in basis points')
        plt.legend()
        plt.show()
        
        
    def get_forward_yields(self, dates, plot=False):
        """ Gets forward yields """
        maturities = utils.time_difference_years_from_list(dates, self._today)
        rates = self._curve(maturities)
        rates = np.divide(rates, 10000)
        interests = np.power(np.add(1, rates), maturities)
        interests_shifted = np.concatenate(([1], np.roll(interests, shift=1)[1:]))
        forwards = np.multiply(np.add(np.divide(interests, interests_shifted), -1), 10000)
        
        if plot:
            self._plot_forward_yields(dates, forwards)
            
        return pd.DataFrame({"date": dates, "rate": forwards})
    
    
    def _plot_forward_yields(self, dates, rates):
        """ Plots forward yields """
        plt.scatter(dates, rates, label='Forward Yields',
                    marker='o', color='black', s=10)
        plt.plot(dates, rates, color='gray', linestyle='-')
        plt.title('Forward Yields vs Maturity Dates')
        plt.xlabel('Marurity date')
        plt.ylabel('Yield in basis points')
        plt.legend()
        plt.show()
        
        
    def get_floating_yields(self, repayment_dates, repricing_dates, plot=False):
        """ 
        Gets variable (floating) yields for assets (loans)
        on repayment_dates when repriced on repricing dates
        """
        repayment_dates_df = pd.DataFrame({'date': repayment_dates})
        forward_yields_og = self.get_forward_yields(repricing_dates, plot=False)
        forward_yields = pd.merge(repayment_dates_df, forward_yields_og, on='date', how='outer')
        spot_yields = self.get_spot_yields(repricing_dates, plot=False)
        forward_yields.at[0,'rate'] = spot_yields.at[0,'rate']
        forward_yields = forward_yields.sort_values(by='date')
        forward_yields['rate'].fillna(method='ffill', inplace=True)
        forward_yields = forward_yields[forward_yields['date'].isin(repayment_dates)]
        
        if plot:
            self._plot_floating_yields(forward_yields['date'], forward_yields['rate'])
    
        return forward_yields
    
    
    def _plot_floating_yields(self, dates, rates):
        """ Plots floating yields """
        plt.scatter(dates, rates, label='Floating Yields',
                    marker='o', color='black', s=10)
        plt.plot(dates, rates, color='gray', linestyle='-')
        plt.title('Floating Yields vs Maturity Dates')
        plt.xlabel('Marurity date')
        plt.ylabel('Yield in basis points')
        plt.legend()
        plt.show()
        