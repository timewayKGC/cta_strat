import talib as ta
import numpy as np
import pandas as pd

"""
Open Range signals
"""

class OPSignal():

    def __init__(self):
        self.author = 'diwei'
    
    #band has different timeframe with breakBand scenario
    def BandCalc(self, am):
        range = am.high[-2] - am.low[-2]
        UpperBand = am.open[-1] + range
        LowerBand = am.open[-1] - range
        return UpperBand, LowerBand
    
    def breakBand(self,am, Upper, Lower):
        breakUpper = am.close[-2] < Upper and am.close[-1] > Upper
        breakLower = am.close[-2] > Lower and am.close[-1] < Lower
        # what is I want to change am.close to tick price?
        #at the moment of the band break, open positions.
        Signal = 0
        if breakUpper:
            Signal = 1
        elif breakLower:
            Signal = -1
        else:
            Signal = 0
        return Signal
    
        