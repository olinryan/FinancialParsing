''' Present an interactive function explorer with slider widgets.

Scrub the sliders to change the properties of the ``sin`` curve, or
type into the title text box to update the title of the plot.

Use the ``bokeh serve`` command to run the example by executing:

    bokeh serve sliders.py

at your command prompt. Then navigate to the URL

    http://localhost:5006/sliders

in your browser.

'''
import numpy as np
import pandas as pd

import os
import sys

from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Slider, TextInput,DatetimeTickFormatter
# from bokeh.plotting import figure, output_file, show, save

import bokeh.plotting as bok

import checkRemote  

import nasdaqdatalink as ndl        # need to pay $$$ for this to work

from polygon import RESTClient      # works ok, only goes back 2 yrs
client = RESTClient(api_key="OMm1HSK6uHOCDVcSmDVkppqS3e1CyxpM")

import pandas_datareader as pdr     # some issues with env packages
import datetime 

class security():
    def __init__(self,ticker,start,end):
        self.ticker = ticker
        self.start = start
        self.end = end
        self.pullData()
        self.calculateDailys()

    def pullData(self):
        '''
        pulls data from specifed ticker (minute base) and date range into a dataframe and returns
        Data will be trunkated to only go back 2 years, bc some nonsense about needing to pay $ for more

        
        '''

        # data = ndl.get_table('ETFG/FUND',date='2023-01-03', ticker='DFEN')
        # data = ndl.get_table('ZACKS/FC', ticker='AAPL')
        
        # data = pdr.get_data_yahoo('AAPL', start=datetime.datetime(2006, 10, 1), end=datetime.datetime(2012, 1, 1))
        
        if not os.path.isdir("__tkr_cache__/"): os.makedirs('__tkr_cache__')

        dataname = f'{self.ticker}_{self.start}_{self.end}'
        datafile = os.path.join("__tkr_cache__",f'{dataname}.pkl')
        if os.path.exists(datafile):
            print(f'Data exists in: {datafile}, reading from local ... ')
            aggs = pd.read_pickle(datafile)
        else:
            print(f'Reading {self.ticker} from polygon ... ')
            # List Aggregates (Bars)
            aggs = []
            try:
                for a in client.list_aggs(ticker=self.ticker, multiplier=1, timespan="minute", from_=self.start, to=self.end, limit=50000):
                # for a in client.list_aggs(ticker="DFEN", multiplier=1, timespan="minute", from_="2020-05-29", to="2024-10-11", limit=50000):
                    aggs.append(a)
            except urllib3.exceptions.MaxRetryError:
                print("Exceeded polygon requests, try again later.")
                sys.exit()

            aggs = pd.DataFrame(aggs)
            aggs['timestamp'] = pd.to_datetime(aggs['timestamp'],unit='ms')
            print(f"Saving to {datafile} ... ")
            aggs.to_pickle(datafile)

        self.aggs = aggs

    def calculateDailys(self):
        # print(self.aggs)
        self.day_op_cl_aggs = self.aggs.resample('B',on='timestamp').agg(['first','last'])
        self.vol_day_aggs = self.aggs.resample('B',on='timestamp').sum()
        self.vol_day_aggs = self.vol_day_aggs.drop(['open','high','low','close','vwap','otc'],axis=1)
        self.vol_day_aggs['change'] = self.day_op_cl_aggs['close']['last'] - self.day_op_cl_aggs['close']['first']
        self.vol_day_aggs['pcnt_change'] = self.vol_day_aggs['change']/self.day_op_cl_aggs['close']['first'] * 100
        
        self.vol_day_aggs['cum_daily_return'] = (1 + self.vol_day_aggs['pcnt_change']/100).cumprod()
        # print(self.day_op_cl_aggs)
        # print(self.vol_day_aggs)

    def calculateRolling(self,period):
        try:
            self.aggs = self.aggs.drop(['rolling_close'],axis=1)
        except KeyError:
            pass
        self.aggs['rolling_close'] = self.aggs['close'].rolling(int(period)).mean()

def createPlot():
    '''
    given a dataframe with some timeseries securities data, create a bokeh plot
    Run this with bokeh serve algorithmicTrading.py --address 0.0.0.0 --port 5006
    open the link in browser
    '''

    # Generate the output file in the browser
    bok.output_file("Securities_Workspace.html", title="Financial Trading Algorithms")
    
    # Set up widgets
    text = TextInput(title="Ticker", value='DFEN')
    SMA1 = Slider(title="Simple Moving Average P1", value=1000.0, start=0.0, end=50000.0, step=1000.0)
    SMA2 = Slider(title="Simple Moving Average P2", value=20000.0, start=0.0, end=50000.0, step=1000.0)

    # Set up price plot 
    PricePlot = bok.figure(height=400, title=f'{text.value} Price $USD', sizing_mode='stretch_width',tools="crosshair")

    # Set up % change plot
    PcntPlot = bok.figure(height=400, title=f'{text.value} Daily % Change', sizing_mode='stretch_width') #,tools="crosshair,pan,reset,save,wheel_zoom", y_axis_type="log"
    
    
    # Set up callbacks
    data = security(ticker=text.value,start="2020-05-29", end="2024-10-11")

    # Price Data:
    sourcePrice = ColumnDataSource(data=dict(x=data.aggs['timestamp'], y=data.aggs['close']))
    PricePlot.line('x', 'y', source=sourcePrice,line_width=3, line_alpha=0.6,color='lime')
    data.calculateRolling(SMA1.value)
    sourceSMA1 = ColumnDataSource(data=dict(x=data.aggs['timestamp'], y=data.aggs['rolling_close']))
    PricePlot.line('x', 'y', source=sourceSMA1,line_width=3, line_alpha=0.6,color='black')
    data.calculateRolling(SMA2.value)
    sourceSMA2 = ColumnDataSource(data=dict(x=data.aggs['timestamp'], y=data.aggs['rolling_close']))
    PricePlot.line('x', 'y', source=sourceSMA2,line_width=3, line_alpha=0.6,color='red')
    PricePlot.xaxis.formatter = DatetimeTickFormatter(days="%Y-%m-%d", months="%Y-%m", hours="%H:%M")

    # Percent Data:
    sourcePcnt = ColumnDataSource(data=dict(x=data.vol_day_aggs.index, y=data.vol_day_aggs['pcnt_change']))
    PcntPlot.line('x', 'y', source=sourcePcnt,line_width=3, line_alpha=0.6,color='blue')
    # source = ColumnDataSource(data=dict(x=data.vol_day_aggs.index, y=data.vol_day_aggs['cum_daily_return']))
    # PcntPlot.line('x', 'y', source=source,line_width=3, line_alpha=0.6,color='pink')
    PcntPlot.xaxis.formatter = DatetimeTickFormatter(days="%Y-%m-%d", months="%Y-%m", hours="%H:%M")


    # def update_SMAs(attrname, old, new):

    #     # Get the current slider values
    #     a = SMA1.value
    #     b = SMA2.value
    #     w = phase.value
    #     k = freq.value

    #     # Generate the new curve
    #     x = np.linspace(0, 4*np.pi, N)
    #     y = a*np.sin(k*x + w) + b

    #     source.data = dict(x=x, y=y)

    def update_company(attrname, old, new):
        data = security(ticker=text.value,start="2020-05-29", end="2024-10-11")
        # Price Data:
        sourcePrice.data = dict(x=data.aggs['timestamp'], y=data.aggs['close'])
        data.calculateRolling(SMA1.value)
        sourceSMA1.data = dict(x=data.aggs['timestamp'], y=data.aggs['rolling_close'])
        data.calculateRolling(SMA2.value)
        sourceSMA2.data = dict(x=data.aggs['timestamp'], y=data.aggs['rolling_close'])

    def update_plot1(attrname, old, new):
        data.calculateRolling(SMA1.value)
        sourceSMA1.data = dict(x=data.aggs['timestamp'], y=data.aggs['rolling_close'])
    def update_plot2(attrname, old, new):
        data.calculateRolling(SMA2.value)
        sourceSMA2.data = dict(x=data.aggs['timestamp'], y=data.aggs['rolling_close'])

    # Recognize Change:
    text.on_change('value', update_company)
    SMA1.on_change('value', update_plot1)
    SMA2.on_change('value', update_plot2)

    # Set up layouts and add to document
    inputs = column(text, SMA1, SMA2)  

    curdoc().add_root(row(column(PricePlot, inputs,sizing_mode='stretch_width'),PcntPlot,sizing_mode='stretch_width'))
    curdoc().title = "Securities Data"
    # bok.show(plot)

    # # Show the plot in the browser tab
    # if not checkRemote.is_running_remotely():
    #     plt.show(plot)
    # else:    
    #     plt.save(plot) 

# Indirect call:
createPlot()


if __name__ == "__main__":
    # data = security(ticker="DFEN",start="2020-05-29", end="2024-10-11")
    createPlot()