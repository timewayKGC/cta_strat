import talib as ta
import numpy as np
import pandas as pd

"""
"""

class DonSignal():

    def __init__(self):
        self.author = 'diwei'

    def emaEnvironment(self, am, paraDict):
        envPeriod = paraDict["envPeriod"]
        envEMA = ta.EMA(am.close, envPeriod)
        envDirection = 1 if am.close[-1]>envEMA[-1] else -1
        return envDirection, envEMA

    def breakBand(self,am,paraDict):
        bandPeriod = paraDict["bandPeriod"]

        hhv = ta.MAX(am.high, bandPeriod)
        llv = ta.MIN(am.low, bandPeriod)
        breakUpper = am.close[-1]>=hhv[-2] and am.close[-2]<hhv[-3]
        breakLower = am.close[-1]<=llv[-2] and am.close[-2]>llv[-3]

        breakBandSignal = 0
        if breakUpper:
            breakBandSignal = 1
        elif breakLower:
            breakBandSignal = -1
        else:
            breakBandSignal = 0
        return breakBandSignal, hhv, llv
    
    def atrExit(self, am, paraDict):
        atrPeriod = paraDict['atrPeriod']
        atr = ta.ATR(am.high, am.low, am.close, atrPeriod)
        return atr
        