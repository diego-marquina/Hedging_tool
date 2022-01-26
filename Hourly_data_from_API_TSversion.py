#%% 
# import modules
from numpy import arange
import pandas as pd
import time
import datetime
from razorshell.api_market_data import MarketDataAPI
api_client = MarketDataAPI("diego.marquina@shell.com", "mddpwd_Diego1", timeout=300)
import seaborn as sns
from plotly.offline import init_notebook_mode, iplot
from plotly.graph_objs import *
init_notebook_mode(connected=True) 
pd.options.plotting.backend = "plotly"

# df = api_client.get_analysis_group_curves(analysis_group_ids='781')
# curve_list = []
# for i in arange(1990,2020):
#     curve_list.append('1Base_Wx-Years.Germany.Generation.All.'+str(i))
#%%
# pull hourly wind and price data data from market data dashboard using API

asof_date = '2021-09-18'
# asof_date = datetime.date.today()

df_price = api_client.get_time_series(
    group_name="1Base_Wx-Years.Great Britain.System Marginal Price",
    start="2022-01-01",
    end="2023-01-01", 
    granularity='hours',
    asof = asof_date
    )

df_wind = api_client.get_time_series(
    group_name="1Base_Wx-Years.Great Britain.Generation",
    start="2022-01-01",
    end="2023-01-01", 
    granularity='hours',
    asof = asof_date
    )

# #%% get model run data
# tic = time.time()
# df2 = api_client.get_model_run_data(run_id=2569,start='2022-01-01', end='2022-04-01')
# toc = time.time()
# print(toc-tic)

# %%
# rename columns and add 'q' column for hedging quantity as percentage of wind
df_price.columns = df_price.columns.str[-4:]
df_price.sort_index(axis=1, inplace=True)
df_wind.columns = df_wind.columns.str[-4:]
df_wind.sort_index(axis=1, inplace=True)

df_price['q'] = 1
df_wind['q'] = 1
# %%
# calculate cash and define timeframe (eg monthly, yearly)
df_cash = df_wind*df_price

timeframe = 'YS' # can be 'd' for day, 'MS' for month or 'YS' for year
time_period = {'YS':'Y','MS':'M'}
df_captured = df_cash.resample(timeframe).sum()/df_wind.resample(timeframe).sum()
df_captured['q'] = 1
# %%
# resample dataframes to desired timeframe
df_baseload = df_price.resample(timeframe).mean()
df_wind_t = df_wind.resample(timeframe).sum()

df_baseload['q'] = 1
df_wind_t['q'] = 1
#%%
# do calculations at different 'q' levels
df_qht = df_wind_t*0
df_qh = df_wind*0
# df_qht = pd.DataFrame(0, index=df_wind_t.index, columns=df_wind_t.columns)
for fh in arange(0.01,1.01,.01):
    df_qht = df_qht.append(df_wind_t*fh)
    df_qh = df_qh.append(df_wind*fh)
# %%
# pre-calculations for P&L
df1 = (df_qht*df_baseload).rename_axis('MyIdx').sort_values(by = ['q', 'MyIdx'], ascending = [True, True])
df_hourly_diff = (df_wind - df_qh)
df_hourly_diff['q'] = 1-df_hourly_diff['q']
df2 = (df_hourly_diff*df_price).rename_axis('MyIdx').sort_values(by = ['q', 'MyIdx'], ascending = [True, True])
df2 = df2.groupby([df2.index.to_period(time_period[timeframe]),'q']).sum().reset_index().set_index('MyIdx').sort_values(by = ['q', 'MyIdx'], ascending = [True, True])[df1.columns]
df2.index = df2.index.to_timestamp()
# %%
#  estimate P&L and Standard Dev
df3 = df1+df2+df_captured*df_wind_t
df3['q'] = (df3['q']-1)/2
df3 = df3.rename_axis('MyIdx').sort_values(by = ['q', 'MyIdx'], ascending = [True, True])

df_pl = df3.drop(columns='Mean').groupby(['q','MyIdx']).sum()
df_std = df_pl.std(axis=1).unstack('q')
sns.heatmap(df_std)
# %%
