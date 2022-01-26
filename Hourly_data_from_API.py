# %%
# import modules
from numpy import arange
import pandas as pd
import time
import datetime
from pandas.core.frame import DataFrame
from razorshell.api_market_data import MarketDataAPI
api_client = MarketDataAPI("diego.marquina@shell.com", "mddpwd_Diego1", timeout=300)
import seaborn as sns
from plotly.offline import init_notebook_mode, iplot
import plotly.graph_objects as go
init_notebook_mode(connected=True) 
pd.options.plotting.backend = "plotly"

# %%
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

# %%
# rename columns and add 'q' column for hedging quantity as percentage of wind
df_price.columns = df_price.columns.str[-4:]
df_price.sort_index(axis=1, inplace=True)
df_wind.columns = df_wind.columns.str[-4:]
df_wind.sort_index(axis=1, inplace=True)

# %%
# calculate cash and define timeframe (eg monthly, yearly)
df_cash = df_wind*df_price

timeframe = 'MS' # can be 'd' for day, 'MS' for month or 'YS' for year
time_period = {'YS':'Y','MS':'M'}
df_captured = df_cash.resample(timeframe).sum()/df_wind.resample(timeframe).sum()

# %%
# resample dataframes to desired timeframe
df_baseload = df_price.resample(timeframe).mean()
df_wind_t = df_wind.resample(timeframe).sum()

# %%
# define P&L caclculation
def calculate_pl(hedge_percentage: float,
                    fwd_price = df_baseload.mean(axis=1),
                    # buy_price: float,
                    # buy_volume: float
                    ):
    hedge_volume = hedge_percentage*df_wind_t.mean(axis=1)
    baseload_hedge = (-1*df_baseload.sub(fwd_price, axis=0)).mul(hedge_volume, axis=0)
    contract_payoff = df_wind_t.mul(df_captured.mean(axis=1), axis=0)
    spot_income = df_wind_t*df_captured
    df_pl = baseload_hedge-contract_payoff+spot_income
    std_dev = df_pl.std(axis=1)
    return df_pl, std_dev

def calculate_pl_ts(hedge_percentage: float,
                    fwd_price = df_baseload.mean(axis=1),
                    buy_price = df_captured.mean(axis=1),
                    buy_volume = df_wind.resample(timeframe).mean().mean(axis=1),
                    ):
    hedge_volume = hedge_percentage*buy_volume
    hedge_volume[df_wind.index[-1]] = hedge_volume.iloc[-1]
    hedge_volume = hedge_volume.resample('h').ffill()
    buy_volume[df_wind.index[-1]] = buy_volume.iloc[-1]
    buy_volume = buy_volume.resample('h').ffill()
    fwd_price[df_wind.index[-1]] = fwd_price.iloc[-1]
    fwd_price = fwd_price.resample('h').ffill()
    buy_price[df_wind.index[-1]] = buy_price.iloc[-1]
    buy_price = buy_price.resample('h').ffill()
    df_hedge = hedge_volume*fwd_price
    df_spot = df_wind.sub(hedge_volume, axis=0)*df_price
    df_captured = df_wind.mul(buy_price, axis=0)
    df_pl = df_spot.add(df_hedge, axis=0)-df_captured
    std_dev = df_pl.resample(timeframe).sum().std(axis=1)
    return df_pl.resample(timeframe).sum(), std_dev

    

# %%
# do calculations at different 'q' levels

df_std = pd.DataFrame()
df_pl = pd.DataFrame()
df_std_ts = pd.DataFrame()
df_pl_ts = pd.DataFrame()
for i in arange(0,1,.01):
    a, df_std[i] = calculate_pl(hedge_percentage=i)
    df_pl[i] = a.sum()
    b, df_std_ts[i] = calculate_pl_ts(hedge_percentage=i)
    df_pl_ts[i] = b.sum()

# %%
# 3D Plot
z = df_std.values/1e6
x = df_std.columns.values
y = df_std.index
# sh_0, sh_1 = z.shape
# x, y = np.linspace(0, 1, sh_0), np.linspace(0, 1, sh_1)
fig = go.Figure(data=[go.Surface(z=z, x=x, y=y)])
# fig.update_layout(title='Standard deviation', autosize=True)
fig.update_traces(contours_z=dict(show=True, usecolormap=True,
                                  highlightcolor="limegreen", project_z=True))
fig.update_traces(contours = {
        "x": {"show": True, "start": 0, "end": 2, "size": 0.04, "color":"white"},
        "y": {"show": True, "start": 0, "end": 11, "size": 1, "color":"white"}})                                  
fig.update_layout(title='Standard deviation', autosize=False,
                  width=500, height=500,
                  margin=dict(l=65, r=50, b=65, t=90))
fig.show()

# %%
# 3D Plot 2
z = df_std_ts.values/1e6
x = df_std_ts.columns.values
y = df_std.index
# sh_0, sh_1 = z.shape
# x, y = np.linspace(0, 1, sh_0), np.linspace(0, 1, sh_1)
fig = go.Figure(data=[go.Surface(z=z, x=x, y=y)])
# fig.update_layout(title='Standard deviation TS', autosize=True)
fig.update_traces(contours_z=dict(show=True, usecolormap=True,
                                  highlightcolor="limegreen", project_z=True))
fig.update_traces(contours = {
        "x": {"show": True, "start": 0, "end": 2, "size": 0.04, "color":"white"},
        "y": {"show": True, "start": 0, "end": 11, "size": 1, "color":"white"}})                                  
fig.update_layout(title='Standard deviation TS', autosize=False,
                  width=500, height=500,
                  margin=dict(l=65, r=50, b=65, t=90))
fig.show()
# %%
