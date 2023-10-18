import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta
import timeutils
from yieldcurve import YieldCurve


def get_present_values(cashflows, market, today):
    """ Get present values for future cashflows """
    table = cashflows.copy()[['id','account','date','cashflow']]
    payment_dates = [date.to_pydatetime() for date in table['date']]
    # GET YIELDS ON PAYMENT DATES
    yieldcurve = YieldCurve(curve_type='EUR01', today=today)
    yieldcurve.fit(market)
    spot_yields = yieldcurve.get_spot_yields(payment_dates)['rate']
    # CALCULATE TIME FROM TODAY TO PAYMENT IN YEARS
    dt = timeutils.time_difference_from_list(payment_dates, today, 'years')
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
    payment_periods = timeutils.date_range(start=maturity_date, end=today, step=1)
    payment_freq = portfolio.at[id, 'payment_freq']
    payment_dates = payment_periods[::payment_freq]
    
    # IF VOLUME THAT IS AFFECTED FROM INTEREST RATE CHANGES FOR EACH MONTH
    if portfolio.at[id, 'ir_binding'] == "FIX":
        volume = np.zeros(months_forward)
    else:
        # DETERMINE REPRICING DATES
        issue_date = portfolio.at[id, 'issue'].to_pydatetime()
        reprice_periods = timeutils.date_range(start=issue_date, end=maturity_date, step=1)
        reprice_freq = portfolio.at[id, 'reprice_freq']
        reprice_dates = pd.Series(reprice_periods[::reprice_freq])
        reprice_dates = reprice_dates[reprice_dates >= today]
        
        if reprice_dates.empty:
            volume = np.zeros(months_forward)
        else:
            reprice_days = timeutils.time_difference_from_list(reprice_dates, today, 'days')
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