#%%

import pandas as pd
import matplotlib.pyplot as plt
from plotly.offline import init_notebook_mode, iplot
from plotly.graph_objs import *
init_notebook_mode(connected=True) 
pd.options.plotting.backend = "plotly"

#%%
df_wind = pd.read_csv('1Base_Wx-Years_wind.csv')
df_price = pd.read_csv('1Base_Wx-Years_price.csv')
dfwp = df_wind.pivot(index='Date',columns='Member',values='Value')
dfwpr = df_price.pivot(index='Date',columns='Member',values='Value')
dfwp.index=pd.to_datetime(dfwp.index, utc=True)
dfwpr.index=pd.to_datetime(dfwpr.index, utc=True)

dfwind2022 = dfwp.loc['2022',:]
dfprice2022 = dfwpr.loc['2022',:]

df_cash2022 = dfwind2022*dfprice2022
capture = df_cash2022.sum()/dfwind2022.sum()
capture = capture.to_frame()
capture.rename(columns={0:'wind captured price'}, inplace=True)
capture['baseload price'] = dfprice2022.mean()
capture['wind discount from baseload'] = capture['baseload price'] - capture['wind captured price']

#%%
capture[['baseload price','wind captured price']].boxplot()
for i,d in enumerate(capture[['baseload price','wind captured price']]):
    y = capture[d]
    x = [i+1]*len(y)
    plt.plot(x, y, mfc = 'orange', mec='k', ms=7, marker='o', linestyle='None')
  
#%%    
capture['wind discount from baseload'].to_frame().boxplot()
for i,d in enumerate(capture['wind discount from baseload'].to_frame()):
    y = capture[d]
    x = [i+1]*len(y)
    plt.plot(x, y, mfc = 'orange', mec='k', ms=7, marker='o', linestyle='None')    
# %%
