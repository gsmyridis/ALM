import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def load_portfolio():
    
    """
    :col id: identification number (the number ofthe row)
    :col account: account type in short
    :col account_name: long account name
    
    :col volume: notional value in EUR
    :col ir_binging: type of the interest binding (FIX or LIBOR)
    :col reprice_freq: repricing frequency in months (if the interest binding is LIBOR)
    :col spread: spread component of the interest rate in basis points
    
    - Cash-flow structure of the products
    :col issue: issue date (this is the first repricing day)
    :col maturity: maturity date
    :col repayment: type of principal repayment structure (bullet, linear, or annuity)
    :col payment_freq: repayment frequency in number of months
    :col yieldcurve: identifier of the interest rate curve
    """
    portfolio = pd.read_csv('data/portfolio.csv')
    portfolio['issue'] = pd.to_datetime(portfolio['issue'])
    portfolio['maturity'] = pd.to_datetime(portfolio['maturity'])
    return portfolio


def load_market():
    
    """
    :col type: yield curve type (for example, yields are from the bond market or the interbank market)
                the type column has to be the same as in portfolio to connect the two datasets
    :col date: maturity of the current rate
    :col rate: value of the rate in basis points
    :col comment: label of the yield curve tensor
    """ 
    market = pd.read_csv('data/market.csv')
    market['date'] = pd.to_datetime(market['date'])
    market['rate'] = market['rate']
    return market


def load_data():
    """ Loads the portfolio and market data """
    return load_portfolio(), load_market()


def set_now():
    """Sets the now date time 30/09/2014"""
    return datetime(2014, 9, 30)


def time_difference_years(date, from_date):
    """ Calculates time defference of date from from_date in years """
    time_difference_seconds = (date-from_date).total_seconds()
    seconds_in_a_year = 60 * 60 * 24 * 365.25
    time_difference_years = time_difference_seconds / seconds_in_a_year
    return time_difference_years


def time_difference_years_from_list(dates, from_date):
    """ Calculated time differences in years for list of dates """
    vectorized_time_difference_years = np.vectorize(time_difference_years, excluded=['from_date'])
    time_differences = vectorized_time_difference_years(dates, from_date=from_date)
    return time_differences
    
    
def datetime_range(start_date, end_date, length):
    """ Returns a range of #length datetimes starting from start_date and ending at end_date """
    # Check the type of start_date
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    elif isinstance(start_date, datetime):
        pass
    else:
        raise TypeError("start_date can be either a string with the format %Y-%m-%d or datetime.datetime")
    # Check the type of end_date
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    elif isinstance(end_date, datetime):
        pass
    else:
        raise TypeError("end_date can be either a string with the format %Y-%m-%d or datetime.datetime")
                      
    time_difference = end_date - start_date
    interval = time_difference / (length - 1)
    date_range = [start_date + i * interval for i in range(length)]
    return date_range

