from nelson_siegel_svensson.calibrate import calibrate_nss_ols

class YieldCurve:
    def __init__(self, curve_type):
        """ Initialize parameters """
        self.curve_type = curve_type
        self._data = None
        self._plot = False
        self._curve = None
        self._status = None
        
    def fit(self, market_data, plot=False):
        """ Fit Nelson-Siegel-Svensson model to the observed yields """
        # Copy market data for the curve type
        self._data = market_data[market_data['type'] == self.curve_type].copy()
        # Calculate time difference in years between now and expiry
        self._data['maturity'] = self._data['date'].apply(lambda date: utils.time_difference_years(date, NOW))
        # Fit the Nelson-Siegel-Svensson model to our yield data
        self._curve, self._status = calibrate_nss_ols(np.ravel(data['maturity']), np.ravel(data['rate']))
        
        self._plot = plot
        if self._plot:
            self._plot_yield()
        
    def _plot_yield(self):
        """ Plot the observed yields and the Nelson-Siegel-Svensson model """
        # Plot observed yield
        plt.scatter(self._data['maturity'], self._data['rate'],
                    label='Observed Yields', marker='o', color='black', s=10)
        # Plot Nelson-Siegel-Svensson model
        plt.plot(self._data['maturity'], self._curve(self._data['maturity']),
                 label='Nelson-Siegel-Svensson', color = 'gray', linestyle='-')
        # Format the figure
        plt.title('Yield Curve')
        plt.xlabel('Maturity time in years')
        plt.ylabel('Yield in %')
        plt.legend()
        # Show plot
        plt.show()