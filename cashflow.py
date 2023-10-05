import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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
    info = {'id': [id] * cashflows.shape[0],
            'account': [portfolio['account'][id]] * cashflows.shape[0],
            'date': payment_dates} 
    cashflows = pd.concat([pd.DataFrame(info), cashflows], axis=1)
    cashflows['date'] = cashflows['date'].dt.to_pydatetime()
#     cashflows.insert(cashflows.shape[1], 'yieldcurve', [portfolio['yieldcurve'][id]] * cashflows.shape[0])
    
    return cashflows


def portfolio_cashflow(portfolio, market, today):
    """ Gets cashflow for each asset in the portfolio and stacks them horizontally """
    port_cashflow = pd.DataFrame()
    for idx, _ in portfolio.iterrows():
        cashflow = asset_cashflow(portfolio=portfolio, market=market, id=idx, today=today)
        port_cashflow = pd.concat([port_cashflow, cashflow], ignore_index=True)
    return port_cashflow
        

def get_present_values(cashflows, market, today):
    """ Get present values for future cashflows """
    table = cashflows.copy()[['id','account','date','cashflow']]
    payment_dates = [date.to_pydatetime() for date in table['date']]
    # GET YIELDS ON PAYMENT DATES
    yieldcurve = YieldCurve(curve_type='EUR01', today=today)
    yieldcurve.fit(market)
    spot_yields = yieldcurve.get_spot_yields(payment_dates)['rate']
    # CALCULATE TIME FROM TODAY TO PAYMENT IN YEARS
    dt = utils.time_difference_from_list(payment_dates, today, 'years')
    # DISCOUNT THE CASHFLOW ON GIVEN DATE TO FIND ITS PRESENT VALUE
    df = (1 + spot_yields/10000)**(-dt)
    table['present_values'] = table['cashflow'] * df
    
    table = table[['id', 'account', 'present_values']]
    table = table.groupby(['id', 'account']).sum().reset_index().set_index('id')
    table.insert(1, 'date', np.full(table.shape[0],  today))
 
    return table


def nii_table(cashflow_table, today, plot=False):
    """ Returns table that breaks down the Net Interest Income (NII) """
    table = cashflow_table.pivot_table(index='date', columns='account', values='interest', aggfunc='sum').reset_index()
    table = table[table['date'] >= today]
    
    # Explicitly select numeric columns (excluding 'date' column) for the sum
    numeric_cols = table.select_dtypes(include=['number']).columns
    table['total'] = table[numeric_cols].sum(axis=1)
    
    table['year'] = table['date'].dt.year
    nii_table = table.groupby('year').sum().T

    if plot:
        # Set up the figure and axis
        fig, ax = plt.subplots(figsize=(12, 8))

        # Bar width and positions
        num_years = len(nii_table.columns)
        width = 0.6
        ind = np.arange(num_years)
        
        bottoms = np.zeros(num_years)

        # Plot vertically stacked bars for each account
        for account in nii_table.index:
            ax.bar(ind, nii_table.loc[account], width, label=str(account), bottom=bottoms)
            bottoms += nii_table.loc[account].values

        # Set axis labels, title, and legend
        ax.set_xlabel('Year')
        ax.set_ylabel('Net Interest Income')
        ax.set_title('Net Interest Income by Year and Account')
        ax.set_xticks(ind)
        ax.set_xticklabels(nii_table.columns, rotation=45, ha='right')
        ax.legend(loc='upper left', bbox_to_anchor=(1,1))

        # Display the plot
        plt.tight_layout()
        plt.show()

    return nii_table


def repricing_gap(portfolio, id, today, months_forward=12):
    """ 
    Calculate repricing gaps of the asset with given id in the given portfolio
    for the months_forard next months
    """
    # CHECK IF months_forward HAS PROPER TYPE
    if not isinstance(months_forward, int):
        raise ValueError("months_forward must be an integer")
    # DETERMINE PAYMENT DATES
    maturity_date = portfolio.at[id, 'maturity'].to_pydatetime()
    payment_periods = utils.date_range(start=maturity_date, end=today, step=1)
    payment_freq = portfolio.at[id, 'payment_freq']
    payment_dates = payment_periods[::payment_freq]
    
    # IF VOLUME THAT IS AFFECTED FROM INTEREST RATE CHANGES FOR EACH MONTH
    if portfolio.at[id, 'ir_binding'] == "FIX":
        volume = np.zeros(months_forward)
    else:
        # DETERMINE REPRICING DATES
        issue_date = portfolio.at[id, 'issue'].to_pydatetime()
        reprice_periods = utils.date_range(start=issue_date, end=maturity_date, step=1)
        reprice_freq = portfolio.at[id, 'reprice_freq']
        reprice_dates = pd.Series(reprice_periods[::reprice_freq])
        reprice_dates = reprice_dates[reprice_dates >= today]
        
        if reprice_dates.empty:
            volume = np.zeros(months_forward)
        else:
            reprice_days = utils.time_difference_from_list(reprice_dates, today, 'days')
            # DETERMINE THE VOLUME FOR EACH MONTH
            idx = np.digitize(reprice_days, np.arange(months_forward+1) * 30)
            volume = (np.bincount(idx[idx<=months_forward], 
                      minlength=months_forward+1)[:months_forward+1] * portfolio.at[id, 'volume'])
    
    return pd.DataFrame({'volume': volume}).drop(0)


def repricing_gap_table(portfolio, today, months_forward=12, plot=False):
    """ 
    Calculate repricing gap table, that is, 
    repricing gap for each month (#months_forward) after doday
    """
    repricing_gaps = [repricing_gap(portfolio, i, today, months_forward) for i in portfolio.index]
    total_gap = pd.concat(repricing_gaps, axis=1).sum(axis=1)
    repricing_gap_df = pd.DataFrame(total_gap, columns=["volume"]).T
    repricing_gap_df.columns = [str(i) + "M" for i in range(1, months_forward+1)]
    
    if plot:
        plt.bar(repricing_gap_df.columns, repricing_gap_df.iloc[0], color='gray')
        plt.xlabel('Months')
        plt.ylabel('EUR')
        plt.title(f"Repricing gap table - Today: {today.date()}")
        plt.tight_layout()
        
    return repricing_gap_df


def liquidity_table(cashflow_table, today, plot=False):
    """ Returns a table with liquidity gaps for each maturity bucket """
    periods_days = [0, 30, 90, 180, 360, 720, 1800, 3600, 7200]
    periods_names = ["1M", "2-3M", "3-6M", "6-12M", "1-2Y", "2-5Y", "5-10Y", ">10Y"]

    cashflow_table = cashflow_table[cashflow_table['date'] >= today]
    cashflows_by_date = cashflow_table.groupby(['date','account']).sum()['cashflow'].reset_index()
    cashflows_by_date['days'] = (cashflows_by_date['date'] - today).dt.days
    cashflows_by_date['period'] = pd.cut(cashflows_by_date['days'], bins=periods_days, labels=periods_names, right=True)
    liquidity_table = cashflows_by_date.groupby(['period','account']).sum().drop(columns=['days']).reset_index()
    liquidity_table = pd.pivot(liquidity_table, index='account', columns='period', values='cashflow')

    if plot:
        # Calculate liquidity gap for each time bucket
        liquidity_gap = liquidity_table.sum(axis=0)
        # Calculate net liquidity position as cumulative liquidity gap
        net_liquidity_position = liquidity_gap.cumsum()
        fig, ax = plt.subplots(figsize=(10, 6))
        # Plot bars for liquidity gap
        ax.bar(liquidity_gap.index, liquidity_gap, label='Liquidity Gap', color='lightgray')

        ax.plot(net_liquidity_position.index, net_liquidity_position, 's--', label='Net Liquidity Position')
        ax.set_xlabel("Time Bucket")
        ax.set_ylabel("Amount")
        ax.set_title("Liquidity Analysis")
        ax.legend()     
        plt.tight_layout()
        plt.show()

    return liquidity_table
