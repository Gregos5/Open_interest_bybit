# Author: Idan Malka
# This code makes use of bybit API (cryptocurrency exchange)
# Requests data of a crypto (default ticker: BTCUSD, 5 min), get price and open interest
# Plots current day along with OI
# Requirements: pandas, numpy, pybit, plotly (from terminal > py -m pip install ...)


import pandas as pd
import numpy as np
import calendar 
from datetime import datetime
from pybit import inverse_perpetual
import plotly.graph_objects as go

def Get_current_day(session, tick_interval=5, ticker='BTCUSD'):
    now = datetime.utcnow()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    since = calendar.timegm(midnight.utctimetuple())
    until = calendar.timegm(now.utctimetuple())

    step = 200*60*tick_interval
    steps = (until-since)/step
    
    step_int = int(np.floor(steps))
    step_fl = steps-step_int

    D_sep = [pd.DataFrame()]*(step_int+1)
    # i full steps 
    for i in range(step_int):
        response = session.query_kline(symbol= ticker, interval= int(tick_interval), **{'from': str(since+i*step)})
        D_sep[i] = pd.DataFrame(response['result'])
    # fracional step
    limit= round(step_fl*200)
    response = session.query_kline(symbol= ticker, interval= int(tick_interval), **{'from': str(since+(step_int)*step)}, limit=limit)
    D_sep[step_int] = pd.DataFrame(response['result'])

    #concatenate segmented df
    D_tot = pd.concat(D_sep)
    D_tot = D_tot.set_index('open_time')
    D_tot = D_tot[['open', 'high', 'low', 'close', 'volume']].astype(float)
    D_tot.rename(columns = { 'open':'Open' , 'high': 'High', 'low': 'Low', 'close':'Close', 'volume':'Volume'}, inplace=True)
    return D_tot

def Get_current_day_oi(session, ticker='BTCUSD', tick_interval=5):
    now = datetime.utcnow()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    since = calendar.timegm(midnight.utctimetuple())
    until = calendar.timegm(now.utctimetuple())

    step = 200*60*tick_interval
    steps = (until-since)/step
    
    step_int = int(np.floor(steps))
    step_fl = steps-step_int

    D_sep = [pd.DataFrame()]*(step_int+1)
    # i full steps 
    for i in range(step_int):
        response = session.open_interest(symbol= ticker, period = str(tick_interval)+"min", **{'from': str(since+i*step)}, limit=200)
        D_sep[i] = pd.DataFrame(response['result'])
    # fracional step
    limit= round(step_fl*200)
    response = session.open_interest(symbol= ticker, period = str(tick_interval)+"min", **{'from': str(since+(step_int)*step)}, limit=limit)
    D_sep[step_int] = pd.DataFrame(response['result'])

    #concatenate segmented df
    D_tot = pd.concat(D_sep)
    D_tot = D_tot.set_index('timestamp')
    D_tot = D_tot[['open_interest']].astype(float)
    return D_tot

def Plot_OI(df, oi):
    df['date'] =  pd.to_datetime(df.index, unit='s', utc=True)
    df = df.set_index('date')

    oi['date'] =  pd.to_datetime(oi.index, unit='s', utc=True)
    oi = oi.set_index('date')

    fig1 = go.Candlestick(
        x=df.index,
        open=df.Open,
        high=df.High,
        low=df.Low,
        close=df.Close,
        xaxis='x',
        yaxis='y2',
        visible=True,
        showlegend=False
    )

    fig2 = go.Line(
        x=oi.index,
        y=oi.open_interest,
        xaxis='x',
        yaxis='y',
        visible=True,
        showlegend=False
    )


    layout = go.Layout(
        title=go.layout.Title(text="BTCUSD today"),
        xaxis=go.layout.XAxis(
            side="bottom",
            title="Date",
            rangeslider=go.layout.xaxis.Rangeslider(visible=False)
        ),
        yaxis=go.layout.YAxis(
            side="right",
            title='OI',
            domain=[0, 0.3]
        ),
        yaxis2=go.layout.YAxis(
            side="right",
            title='Price',
            domain=[0.35, 1.0]
        )
        
    )
    fig = go.Figure(data=[fig1, fig2], layout=layout)
    return fig

public_session = inverse_perpetual.HTTP(endpoint="https://api.bybit.com")

#BTCUSD 5min (5min is the minimum allowed for oi API requests)
period = 5
DayPrice = Get_current_day(public_session, tick_interval=period)
DayOI =  Get_current_day_oi(public_session, tick_interval=period)

fig = Plot_OI(DayPrice, DayOI)
fig.show()