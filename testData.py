'''test pulling pickle data'''
import pandas as pd

import os 
cache = '__tkr_cache__'
    
for f in os.listdir(cache):
    print(f)
    try:
        file = pd.read_pickle(os.path.join(cache,f))
        print(file  )
    except:
        pass