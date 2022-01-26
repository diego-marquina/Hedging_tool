# %%
# import modules
import datetime as dt
from razorshell.api_market_data import MarketDataAPI
from dotenv import load_dotenv
import os
import logging
import pandas as pd

from plotly.offline import init_notebook_mode, iplot
import plotly.graph_objects as go
init_notebook_mode(connected=True) 
pd.options.plotting.backend = "plotly"

cadence = 'MS' # cadence can be 'd' for day, 'MS' for month or 'YS' for year
start: str = '2015-01-01' #start of results
end: str = '2100-01-01' # end of results
# asof_date='2021-11-29 10:00' # model run date
asof_date=dt.date.today() # model run date
api_client = MarketDataAPI(api_password='mddpwd_Diego1', api_user_name='diego.marquina@shell.com', timeout=300)
# pull the hourly wind and solar generation and price from the model outputs for all weather years
df = api_client.get_time_series(
    group_name='RazorShell.1Base_Wx-Years.Captured_price',
    start=start,
    end=end, 
    granularity='hours',
    asof = asof_date
    )


# stack and add columns
df2 = df.stack().reset_index().rename(columns={'level_1':'alias',0:'1Base_Wx-Years'})
df2['region'] = df2.alias.apply(lambda x: x.split('.')[1])
df2['metric'] = df2.alias.apply(lambda x: x.split('.')[2])
df2['tech'] = df2.alias.apply(lambda x: 'NaN' if x.split('.')[3].isnumeric() else x.split('.')[3])
df2['weather_year'] = df2.alias.apply(lambda x: x.split('.')[-1])

logging.info(msg='dataframe stacked for processing')

# separate into dataframes for each metric
df_wind = df2.loc[df2.tech=='Wind'].groupby(['date','region','weather_year']).mean().unstack(['region','weather_year'])
df_solar = df2.loc[df2.tech=='Solar'].groupby(['date','region','weather_year']).mean().unstack(['region','weather_year'])
df_price = df2.loc[df2.metric.str.contains('Price')].groupby(['date','region','weather_year']).mean().unstack(['region','weather_year'])

logging.info(msg='separate into dataframes for each metric')
#%%
df_next = pd.read_csv('Next_profile_from_Nico.csv')
# df_next.index = pd.to_datetime(df_next.Date)+pd.to_timedelta(df_next.Hour_Ending-1, unit='hours')
# df_next = df_next.sort_index()
df_next.index = pd.to_datetime(df_next.Date)
df_next = df_next.loc[:,['Month','Day','Hour_Ending','Value']]
df_next.index.set_names('date', inplace=True)

#%%
# calculate cash
df_wind_cash = df_wind*df_price
df_solar_cash = df_solar*df_price
df_profile_cash = df_price.loc['2022'].mul(df_next['Value'], axis=0)



#calculate captured price
df_wind_captured = df_wind_cash.resample(cadence).sum()/df_wind.resample(cadence).sum()
df_solar_captured = df_solar_cash.resample(cadence).sum()/df_solar.resample(cadence).sum()
df_profile_captured = df_profile_cash.resample(cadence).sum().div(df_next['Value'].resample(cadence).sum(), axis=0)

#%%
df_wind_captured.stack('region').groupby(['region','date']).mean().to_csv('wind_captured.csv')
df_solar_captured.stack('region').groupby(['region','date']).mean().to_csv('solar_captured.csv')
df_price.resample('MS').mean().stack('region').groupby(['region','date']).mean().to_csv('baseload_price.csv')
(df_wind_captured/df_price.resample('MS').mean()).stack('region').groupby(['region','date']).mean().to_csv('wind_profile.csv')
(df_solar_captured/df_price.resample('MS').mean()).stack('region').groupby(['region','date']).mean().to_csv('solar_profile.csv')
(df_profile_captured/df_price.resample('MS').mean()).stack('region').groupby(['region','date']).mean().to_csv('next_profile.csv')
(df_solar_captured/df_profile_captured).stack('region').groupby(['region','date']).mean().to_csv('solar_over_next_profile.csv')

#%%
#for Megha

df_wind.columns = df_wind.columns.set_levels(['Wind'],level=0)
df_solar.columns = df_solar.columns.set_levels(['Solar'],level=0)
df_price.columns = df_price.columns.set_levels(['Price'],level=0)
pd.concat(
    [
        df_wind.loc[:,df_wind.columns.get_level_values(1)=='Netherlands'],
        df_solar.loc[:,df_solar.columns.get_level_values(1)=='Netherlands'],
        df_price.loc[:,df_price.columns.get_level_values(1)=='Netherlands']
    ],
    axis=1
).to_csv('hourly_wind_solar_price_NL.csv')