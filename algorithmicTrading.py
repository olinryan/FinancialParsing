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
from datetime import date

from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Slider, TextInput,DatetimeTickFormatter, HoverTool, Band, DateRangeSlider
from bokeh.palettes import Dark2_5 as palette
import itertools
# from bokeh.plotting import figure, output_file, show, save

import bokeh.plotting as bok

import checkRemote  

import nasdaqdatalink as ndl        # need to pay $$$ for this to work

from polygon import RESTClient      # works ok, only goes back 2 yrs
client = RESTClient(api_key="OMm1HSK6uHOCDVcSmDVkppqS3e1CyxpM")

import pandas_datareader as pdr     # some issues with env packages
import datetime 

class security():
    def __init__(self,datafile):
        self.datafile = datafile
        self.pullData(self.datafile)
        self.calculateTrend()
        self.calculatePctChng()

    def pullData(self, datafile):
        '''
        pulls data from specifed ticker and returns data stored in __tkr_cache__        
        '''
        if os.path.exists(datafile):
            # ensure desired ticker is in the database
            # print(f'Data exists in: {datafile}, reading from local ... ')
            self.aggs = pd.read_pickle(datafile)
        else:
            # give a dataframe that will work but is not valuable
            self.aggs = pd.DataFrame({"timestamp":pd.date_range(start='2023-01-01', end='2023-01-10'),
                                 "close":np.ones(10),"volume":np.ones(10),"low":np.ones(10),
                                 "high":np.ones(10),"open":np.ones(10)})

    def calculateRolling(self,period):
        try:
            self.aggs = self.aggs.drop(['rolling_close'],axis=1)
        except KeyError:
            pass
        self.aggs['rolling_close'] = self.aggs['close'].rolling(int(period)).mean().shift(-int(period))

    def calculateTrend(self):
        '''from first day as base 0% see trend growth %
        i.e. curday - day1 /day1 *100%'''
        day1 = self.aggs["high"].iloc[-1]
        trnd = []
        for i in range(len(self.aggs['high'])):
            trnd.append(((self.aggs['high'].iloc[i] - day1)/day1)* 100)
        self.aggs["trend"] = trnd

    def calculatePctChng(self):
        '''calculate daily % change
        i.e. close - open /open *100%'''
        pctchng = []
        for i in range(len(self.aggs['open'])):
            pctchng.append(((self.aggs['close'].iloc[i] - self.aggs['open'].iloc[i])/self.aggs['open'].iloc[i] )*100)
        self.aggs["pcnt_change"] = pctchng

def createPlots():
    '''
    given a dataframe with some timeseries securities data, create a bokeh plot
    Run this with bokeh serve algorithmicTrading.py --address 0.0.0.0 --port 5006
    open the link in browser
    '''

    cache = '__tkr_cache__/'
    # Generate the output file in the browser
    bok.output_file("Securities_Workspace.html", title="Financial Trading Algorithms")
    
    # Set up widgets
    text = TextInput(title="Ticker:", value='BA')
    SMA1 = Slider(title="Simple Moving Average P1 (Days)", value=50.0, start=0.0, end=2500.0, step=10.0)
    SMA2 = Slider(title="Simple Moving Average P2 (Days)", value=150.0, start=0.0, end=2500.0, step=10.0)

    text_mrkt = TextInput(title="Use as Market:",value = 'IVV')
    DRS_beta = DateRangeSlider(value=(date(2020, 1, 1), date(2021, 12, 31)),
                                    start=date(2012, 1, 1), end=date.today())

    # Set up Trend plot
    TrendPlot = bok.figure(height=800, title='Portfolio Trend From Start, Daily High', sizing_mode='stretch_width',tools="crosshair,wheel_zoom,box_zoom,reset")

    # Set up price plot 
    PricePlot = bok.figure(height=400, title='Security Price $USD', sizing_mode='stretch_width',tools="crosshair")

    # Set up % change plot
    PcntPlot = bok.figure(height=600, title='Security Daily % Change', sizing_mode='stretch_width') #,tools="crosshair,pan,reset,save,wheel_zoom", y_axis_type="log"
    
    # Set up Beta Plot
    BetaPlot = bok.figure(height=1200, width = 1200, title='Market Correlation, Past 600 days',tools="crosshair,wheel_zoom,box_zoom,reset")

    #colors has a list of colors which can be used in plots 
    colors = itertools.cycle(palette) 

    ##################################################################################################
    # Trend Data:
    for sec in os.listdir(cache):
        if sec.endswith("_quote.pkl"):
            ticker = sec.split('_')[0]
            data = security(datafile=os.path.join(cache,sec))
            sourceTrnd = ColumnDataSource(data=dict(x=data.aggs['timestamp'], y=data.aggs['trend']))
            TrendPlot.line('x','y',source=sourceTrnd,line_width=3, line_alpha=0.6,name=ticker,legend_label = ticker,color=next(colors))
    TrendPlot.xaxis.formatter = DatetimeTickFormatter(days="%Y-%m-%d", months="%Y-%m", hours="%H:%M")
    hover = HoverTool(tooltips = [('Ticker','$name'),('% Change','@y'),('Date','@x')])
    TrendPlot.add_tools(hover)

    ##################################################################################################
    # Set up callbacks
    data = security(datafile=os.path.join(cache,f'{text.value}_quote.pkl'))
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
    sourcePcnt = ColumnDataSource(data=dict(x=data.aggs['timestamp'], y=data.aggs['pcnt_change']))
    sourcemean = ColumnDataSource(data=dict(x=data.aggs['timestamp'], y=np.full(len(data.aggs['timestamp']),np.mean(data.aggs['pcnt_change']))))
    sourcestdp = ColumnDataSource(data=dict(x=data.aggs['timestamp'], y=np.full(len(data.aggs['timestamp']),np.mean(data.aggs['pcnt_change']) + np.std(data.aggs['pcnt_change']))))
    sourcestdm = ColumnDataSource(data=dict(x=data.aggs['timestamp'], y= np.full(len(data.aggs['timestamp']),np.mean(data.aggs['pcnt_change']) - np.std(data.aggs['pcnt_change']))))
    PcntPlot.scatter('x', 'y', source=sourcePcnt,color='blue')
    PcntPlot.line('x', 'y',source=sourcemean,line_width=3,color = 'red')

    # df = pd.DataFrame(data=dict(x=data.aggs['timestamp'], y=data.aggs['pcnt_change']))

    # sem = lambda x: x.std() / np.sqrt(x.size)
    # df2 = df.y.rolling(window=int(SMA1.value)).agg({"y_mean": 'mean', "y_std": 'std', "y_sem": sem})
    # df2 = df2.bfill()

    # df = pd.concat([df, df2], axis=1)
    # df['lower'] = df.y_mean - df.y_std
    # df['upper'] = df.y_mean + df.y_std

    # sourcerolstd = ColumnDataSource(df.reset_index())

    # band = Band(base='x', lower='lower', upper='upper', source=sourcerolstd, level='underlay',
    #             fill_alpha=1.0, line_width=3, line_color='red',line_dash='dashed')
    # PcntPlot.add_layout(band)

    PcntPlot.line('x', 'y',source=sourcestdp,color = 'black',line_width=3,line_dash='dashed')
    PcntPlot.line('x', 'y',source=sourcestdm,color = 'black',line_width=3,line_dash='dashed')
    PcntPlot.xaxis.formatter = DatetimeTickFormatter(days="%Y-%m-%d", months="%Y-%m", hours="%H:%M")

    ##################################################################################################
    # Risk Data:
    data_mkt = security(datafile=os.path.join(cache,f'{text_mrkt.value}_quote.pkl'))
    # print(data_mkt.aggs)
    for sec in os.listdir(cache):
        if sec.endswith("_quote.pkl"):
            ticker = sec.split('_')[0]
            data_reg = security(datafile=os.path.join(cache,sec))
            sourceBta = ColumnDataSource(data=dict(x=data_mkt.aggs['pcnt_change'].loc[:600], y=data_reg.aggs['pcnt_change'].loc[:600]))
            BetaPlot.scatter('x','y',source=sourceBta,name=ticker,legend_label = ticker,color=next(colors))
    hover = HoverTool(tooltips = [('Ticker','$name')])
    BetaPlot.add_tools(hover)

    def update_company(attrname, old, new):
        global data
        data = security(datafile=os.path.join(cache,f'{text.value}_quote.pkl'))
        # Price Data:
        sourcePrice.data = dict(x=data.aggs['timestamp'], y=data.aggs['close'])
        data.calculateRolling(SMA1.value)
        sourceSMA1.data = dict(x=data.aggs['timestamp'], y=data.aggs['rolling_close'])
        data.calculateRolling(SMA2.value)
        sourceSMA2.data = dict(x=data.aggs['timestamp'], y=data.aggs['rolling_close'])
        sourcePcnt.data = dict(x=data.aggs['timestamp'], y=data.aggs['pcnt_change'])
        sourcemean.data = dict(x=data.aggs['timestamp'], y=np.full(len(data.aggs['timestamp']),np.mean(data.aggs['pcnt_change'])))
        sourcestdp.data = dict(x=data.aggs['timestamp'], y=np.full(len(data.aggs['timestamp']),np.mean(data.aggs['pcnt_change']) + np.std(data.aggs['pcnt_change'])))
        sourcestdm.data = dict(x=data.aggs['timestamp'], y= np.full(len(data.aggs['timestamp']),np.mean(data.aggs['pcnt_change']) - np.std(data.aggs['pcnt_change'])))
        update_plot1
        update_plot2

    def update_plot1(attrname, old, new):
        data = security(datafile=os.path.join(cache,f'{text.value}_quote.pkl'))
        data.calculateRolling(SMA1.value)
        sourceSMA1.data = dict(x=data.aggs['timestamp'], y=data.aggs['rolling_close'])

        # df = pd.DataFrame(data=dict(x=data.aggs['timestamp'], y=data.aggs['pcnt_change']))
        
        # df2 = df.y.rolling(window=int(SMA1.value)).agg({"y_mean": 'mean', "y_std": 'std', "y_sem": sem})
        # df2 = df2.bfill()

        # df = pd.concat([df, df2], axis=1)
        # df['lower'] = df.y_mean - df.y_std
        # df['upper'] = df.y_mean + df.y_std

        # sourcerolstd.data = df.reset_index()

    def update_plot2(attrname, old, new):
        data = security(datafile=os.path.join(cache,f'{text.value}_quote.pkl'))
        data.calculateRolling(SMA2.value)
        sourceSMA2.data = dict(x=data.aggs['timestamp'], y=data.aggs['rolling_close'])

    def update_risk(attrname, old, new):
        data_mkt = security(datafile=os.path.join(cache,f'{text.value}_quote.pkl'))
        for sec in os.listdir(cache):
            if sec.endswith("_quote.pkl"):
                ticker = sec.split('_')[0]
                data_reg = security(datafile=os.path.join(cache,sec))
                sourceBta.data = dict(x=data_mkt.aggs['pcnt_change'].iloc[:600], y=data_reg.aggs['pcnt_change'].iloc[:600])
    
    # Recognize Change:
    text.on_change('value', update_company)
    SMA1.on_change('value', update_plot1)
    SMA2.on_change('value', update_plot2)

    text_mrkt.on_change('value', update_risk)

    # Set up layouts and add to document
    inputs = column(text, SMA1, SMA2)  

    tradingPlt = row(column(PricePlot, inputs,sizing_mode='stretch_width'),PcntPlot,sizing_mode='stretch_width')
    
    riskPlt = row(column(text_mrkt,DRS_beta),BetaPlot,sizing_mode='stretch_width')

    curdoc().add_root(column(TrendPlot,tradingPlt,riskPlt,sizing_mode='stretch_width'))
    curdoc().title = "Securities Data"

# Indirect call:
createPlots()


if __name__ == "__main__":
    # data = security(ticker="DFEN",start="2020-05-29", end="2024-10-11")
    createPlots()