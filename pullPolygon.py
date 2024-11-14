"""
Pull quote data from polygon API dayly and update local database in __tkr_cache__

These are the quotes interested:
    AAPL    Apple Co.
    BA      Boeing Co.
    DFEN    Direxion Daily Aerospace & Defense Bull 3X Shares
    DIA     SPDR Dow Jones Industrial Average ETF Trust
    GD      General Dynamics
    GE      General Electric
    HWM     Howmet Aerospace Inc.
    IVV     iShares Core S&P 500 ETF
    LHX     L3Harris Technologies Inc.
    LMT     Lockheed Martin Corp
    NOC     Northrop Grumman Corp
    RTX     Raytheon Technologies
    SPR     Spirit AeroSystems Holdings Inc
"""
import os
import re
import sys
import datetime
import time

import pandas as pd

from polygon import RESTClient      # works ok, only goes back 2 yrs
client = RESTClient(api_key="OMm1HSK6uHOCDVcSmDVkppqS3e1CyxpM")

def loadData():
    '''
    load data from csv in NYSE_export folder and save as pkl
    '''

    cache = '__tkr_cache__/NYSE_export'
    
    for f in os.listdir(cache):
        data = pd.read_csv(os.path.join(cache,f))
        dataname = f'__tkr_cache__/{f.split('.')[0]}_quote.pkl'
        data['timestamp']   = pd.to_datetime(data['Date'])
        cols = ['Close/Last','Open', 'High', 'Low']  
        data[cols] = data[cols].astype(str)
        data['close']       = data['Close/Last'].apply(lambda x: re.sub('\\$', '', x))
        data['open']        = data['Open'].apply(lambda x: re.sub('\\$', '', x))
        data['high']        = data['High'].apply(lambda x: re.sub('\\$', '', x))
        data['low']         = data['Low'].apply(lambda x: re.sub('\\$', '', x))
        data['volume']      = data['Volume']
        cols = ['close','open', 'high', 'low']  
        data[cols] = data[cols].astype(float)
        data.drop(['Date','Volume','Close/Last','Low','High','Open'], axis = 1, inplace = True)
        data.to_pickle(dataname)

def pullData():
    '''
    pull daily data from specifed ticker into a dataframe and merge with existing picklized dataframe        
    '''
    cache = '__tkr_cache__'

    # Get today's date
    today = datetime.date.today()

    # Loop through pkl quote files
    for f in os.listdir(cache):
        if f.endswith("_quote.pkl"):
            ticker = f.split('_')[0]
            datafile = os.path.join(cache,f)
            localdata = pd.read_pickle(datafile)
            lastEntry = localdata['timestamp'][0] + pd.tseries.offsets.Hour(4)
            print(f'Reading {ticker} from polygon ... ')

            aggs = []   # Aggregates frame
            read = True

            # loop until successfully read
            while read:
                # try:
                    # pull most recent full buisness day from database
                    for a in client.list_aggs(ticker=ticker, multiplier=1, timespan="day", from_=lastEntry, to=today, limit=1):
                        aggs.append(a)
                    read = False
                # except:
                    # print("Exceeded polygon requests, Waiting ...")
                    # time.sleep(65)  # polygon has a 5 request per minute cap
           
            aggs = pd.DataFrame(aggs)
            aggs['timestamp'] = pd.to_datetime(aggs['timestamp'],unit='ms')
            aggs['timestamp'] = aggs['timestamp'].dt.normalize()
            aggs.drop(['otc','transactions','vwap'], axis = 1, inplace = True)
            print(aggs)
            # print(localdata)
            if aggs['timestamp'][0] not in localdata['timestamp']:
                mergeddata = pd.concat([aggs,localdata])
                # print(mergeddata)
                print(f"Saving to {datafile} ... ")
            
            mergeddata.to_pickle(datafile)



if __name__ == "__main__":
    # loadData()
    pullData()