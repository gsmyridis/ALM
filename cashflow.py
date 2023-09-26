import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
import utils
from yieldcurve import YieldCurve


def amortization_schedule(rate=0, maturity=1, volume=1, payment_type='BULLET'):
    """ Returns the amortization schedule of the loan """
    if isinstance(rate, (float, int)):
        rate = np.full(maturity, rate)
    
    if payment_type == 'BULLET':
        interest = rate * volume
        capital = np.zeros(maturity)
        capital[-1] = volume
        remaining = np.full(maturity, volume)-capital
        cashflow = capital + interest
    elif payment_type == 'LINEAR':
        # Calculate capital
        capital = np.full(maturity, 1/maturity) * volume
        # Calculate remaining balance after each capital payment
        remaining = np.hstack((volume, volume - np.cumsum(capital)))[:-1]
        # Calculate interest payment for each period
        interest = remaining[:maturity] * rate
        # Calculate total cash flow for each period
        cashflow = capital + interest
    elif payment_type == 'ANNUITY':
        interest = np.zeros(maturity)
        capital = np.zeros(maturity)
        cashflow = np.zeros(maturity)
        remaining = [volume]
        for i in range(maturity):
            discount_factor = 1 - (1 + rate[i]) ** (-(maturity - i + 1))
            cashflow[i] = (rate[i] / discount_factor) * remaining[i] if rate[i] != 0 else remaining[i] / (maturity - i + 1)
            interest[i] = remaining[i] * rate[i]
            capital[i] = cashflow[i] - interest[i]
            remaining.append(remaining[i]-capital[i])
        remaining = remaining[1:]
    else:
        raise TypeError("payment_type can be either BULLET, LINEAR or ANNUITY")
    
    cf_df = pd.DataFrame({'cashflow': cashflow, 'interest': interest, 'capital': capital, 'remaining': remaining})
    return cf_df


def asset_cashflow(portfolio, market, id, today):
    """ Gets cashflow for asset in portfolio with id, given the market """
    # CALCULATE PAYMENT PERIODS
    maturity_date = portfolio['maturity'][id].to_pydatetime()
    payment_periods = utils.date_range(start=maturity_date, end=today, step=1)
    payment_periods = [date for date in payment_periods if date > today]
    # DETERMINE PAYMENT FREQUENCY
    payment_freq = portfolio['payment_freq'][id]
    # SELECT PAYMENT DATES
    payment_dates = payment_periods[::payment_freq]
    payment_dates = payment_dates[::-1]
    # CALCULATE INTEREST RATES
    ir_binding = portfolio['ir_binding'][id]
    spread = portfolio['spread'][id]
    if ir_binding == 'FIX':
        rate = spread
    else:
        # CALCULATE REPRICING PERIODS
        issue_date = portfolio['issue'][id].to_pydatetime()
        reprice_periods = utils.date_range(start=issue_date, end=maturity_date, step=1)
        # DETERMINE REPRICING FREQUENCY
        reprice_freq = portfolio['reprice_freq'][id]
        # SELECT REPRICING DATES
        reprice_dates = reprice_periods[::int(reprice_freq)]
        reprice_dates = [date for date in reprice_dates if date > today]
        
        if len(reprice_dates) > 0:
            # CALCULATE FLOATING YIELDS
            yieldcurve_type = portfolio['yieldcurve'][id]
            yieldcurve = YieldCurve(curve_type=yieldcurve_type, today=today)
            yieldcurve.fit(market)
            forward_yields = yieldcurve.get_floating_yields(repayment_dates=payment_dates,
                                                             repricing_dates=reprice_dates)
            rate = forward_yields['rate'].add(portfolio['spread'][id])
        else:
            rate = spread
        
    # CALCULATE CASHFLOWS
    monthly_rate = (rate / 10000)*(payment_freq / 12)
    maturity = len(payment_dates)
    volume = portfolio['volume'][id]
    repayment = str(portfolio['repayment'][id])
    
    cashflows = amortization_schedule(rate=monthly_rate, maturity=maturity,
                                      volume=volume, payment_type=repayment)
    cashflows.insert(0, 'date', payment_dates)
    
    return cashflows


def portfolio_cashflow(portfolio, market, today):
    """ Gets cashflow for each asset in the portfolio and stacks them horizontally """
    port_cashflow = pd.DataFrame()
    for idx, _ in portfolio.iterrows():
        cashflow = asset_cashflow(portfolio=portfolio, market=market, id=idx, today=today)
        port_cashflow = pd.concat([port_cashflow, cashflow], ignore_index=True)
    return port_cashflow
        
                       