import pandas as pd
import datetime


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
    # Read CSV file
    portfolio = pd.read_csv('data/portfolio.csv')
    # Turn date columns to DateTime type
    portfolio['issue'] = pd.to_datetime(portfolio['issue'])
    portfolio['maturity'] = pd.to_datetime(portfolio['maturity'])
    return portfolio


def load_market():
    
    """
    :col yield: yield curve type (for example, yields are from the bond market or the interbank market)
                the type column has to be the same as in portfolio to connect the two datasets
    :col date: maturity of the current rate
    :col rate: value of the rate in basis points
    :col comment: label of the yield curve tensor
    """ 
    # Read CSV file
    market = pd.read_csv('data/market.csv')
    # Turn date columns to DateTime type
    market['date'] = pd.to_datetime(market['date'])
    return market


def load_data():
    """ Loads the portfolio and market data """
    return load_portfolio(), load_market()


def set_now():
    """Sets the now date time 30/09/2014"""
    return datetime.datetime(2014, 9, 30)


def time_difference_years(date, from_date):
    """ Calculates time defference of date from from_date in years """
    time_difference_seconds = (date-from_date).total_seconds()
    seconds_in_a_year = 60 * 60 * 24 * 365.25
    time_difference_years = time_difference_seconds / seconds_in_a_year
    return time_difference_years

