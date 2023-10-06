import warnings
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


def set_today(date=datetime(2014,9,30)):
    """ Set today's date """
    if not isinstance(date, (datetime, str)):
        raise TypeError("date can be either datetime or a string with the format %Y-%m-%d")
    if isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d")
    return date


def time_difference(date, from_date, unit):
    """ Calculates time defference of date from from_date in years """
    # CHECK IF date TYPE IS PROPER
    if isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d")
    elif isinstance(date, datetime):
        pass
    else:
        raise ValueError(f"""Dates have to be either strings or datetimes. Instead, it is {type(date)}""")
    # CHECK IF from_date TYPE IS PROPER  
    if isinstance(from_date, str):
        from_date = datetime.strptime(from_date, "%Y-%m-%d")
    elif isinstance(from_date, datetime):
        pass
    else:
        raise ValueError(f"""Dates have to be either strings or datetimes. Instead, it is {type(from_date)}""")
    # CHECK IF unit TYPE IS PROPER
    if unit not in ['years', 'days']:
        raise ValueError("unit of time can be either 'years' or 'days'")
    
    # CALCULATE TIME DIFFERENCE
    time_diff = (date-from_date).days
    if unit == 'years':
        time_diff /= 365.25
 
    return time_diff


def time_difference_from_list(dates, from_date, unit):
    """ Calculated time differences in years for list of dates """
    # CHECK IF TYPE OF dates IS PROPER
    if isinstance(dates, pd.Series):
        dates = [pd.to_datetime(d).to_pydatetime() for d in np.ravel(dates)]
    elif isinstance(dates, list):
        pass
    else:
        raise TypeError("dates can be either a list or pandas.Series of datetimes")
    # CALCULATE TIME DIFFERENCES
    vectorized_time_difference = np.vectorize(time_difference, excluded=['from_date', 'unit'])
    time_differences = vectorized_time_difference(dates, from_date=from_date, unit=unit)
    return time_differences

 
def date_range(start=None, end=None, length=None, step=None):
    """ Returns a range of #length datetimes starting from start_date and ending at end_date """
    
    # CHECK THAT NOT ALL PARAMETER ARE NONE
    if (start is None) and (end is None) and (length is None) and (step is None):
        raise ValueError("All parameters are None")
    # CHECK THAT NOT ALL PARAMETERS ARE PROVIDED
    elif (start is not None) and (end is not None) and (length is not None) and (step is not None):
        raise ValueError("You cannot provide all parameters")
        
    # CHECK IF start HAS PROPER TYPE
    if isinstance(start, str):
        start = datetime.strptime(start, '%Y-%m-%d')
    elif isinstance(start, pd._libs.tslibs.timestamps.Timestamp):
        start = start.to_pydatetime()
    elif isinstance(start, datetime) or (start is None):
        pass
    else:
        raise TypeError("start can be either a string with the format %Y-%m-%d or datetime, or None")
    
    # CHECK IF end HAS PROPER TYPE
    if isinstance(end, str):
        end = datetime.strptime(end, '%Y-%m-%d')
    elif isinstance(end, pd._libs.tslibs.timestamps.Timestamp):
        start = end.to_pydatetime()
    elif isinstance(end, datetime) or (end is None):
        pass
    else:
        raise TypeError("end can be either a string with the format %Y-%m-%d or datetime, or None")
        
    # CHECK THAT EITHER length OR step IS PROVIDED
    if (length is None) and (step is None):
        raise ValueError("You have to provide either length or step in months")
    elif (length is not None) and not isinstance(length, int):
        raise TypeError("Integer length must be provided")
    elif (step is not None) and not isinstance(step, int):
        raise TypeError("Integer step must be provided")
    
    # START - END - LENGTH
    if (start is not None) and (end is not None) and (length is not None):
        time_difference = end - start
        interval = time_difference / (length - 1)
        if start < end:
            date_range = [start + i * interval for i in range(length)]
        else:
            date_range = [start - i * interval for i in range(length)]
    
    # START - LENGTH - STEP
    elif (start is not None) and (end is None) and (length is not None) and (step is not None):
        date_range = []
        current_date = start
        for _ in range(length):
            date_range.append(current_date)
            current_date += relativedelta(months=step)
            
    # END - LENGTH - STEP
    elif (end is not None) and (length is not None) and (step is not None) and (start is None):
        date_range = []
        current_date = end
        for _ in range(length):
            date_range.append(current_date)
            current_date -= relativedelta(months=step)
        
    # START - END - STEP
    elif (start is not None) and (end is not None) and (step is not None):
        date_range = []
        current_date = start
        if start < end:
            while current_date <= end:
                date_range.append(current_date)
                current_date += relativedelta(months=step)
        else:
            while current_date >= end:
                date_range.append(current_date)
                current_date -= relativedelta(months=step)
    
    else:
        raise ValueError("""There are only four valid combinations of parameters (start, end, length),
                         (start, length, step), (end, length, step) or (start, end, step)""")
    
    date_range = [datetime(d.year, d.month, d.day) for d in date_range]
    return date_range
