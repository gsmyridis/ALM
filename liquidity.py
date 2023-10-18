import pandas as pd
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta
from yieldcurve import YieldCurve

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