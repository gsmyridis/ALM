import pandas as pd
from matplotlib import pyplot as plt

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
    portfolio.set_index('id', inplace=True)
    portfolio['issue'] = pd.to_datetime(portfolio['issue'])
    portfolio['maturity'] = pd.to_datetime(portfolio['maturity'])
    portfolio['reprice_freq'] = portfolio['reprice_freq'].fillna(1).astype(int)

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


def load_non_maturity_deposits(plot=False):
    """
      Loads Austrian non-maturity deposits data 
    :col date: date of the observation
    :col eur1m: 1-month Euribor
    :col cpn: deposit coupon
    :col bal: end-of-month balance of non-maturity deposits
    """
    data = pd.read_csv('data/ecb_nmd_data.csv')
    data['date'] = pd.to_datetime(data['date'], format='%m/%d/%Y')

    if plot:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(data['date'], data['eur1m'], linestyle='-', label='EUR1M')
        ax.plot(data['date'], data['cpn'], linestyle='--', label='Coupon')
        ax.set_xlabel('Year')
        ax.set_ylabel('Interest Rate (%)')
        ax.legend()

        ax.set_title('Deposit coupon vs 1-month Euribor')
    return data