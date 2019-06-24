"""
strategy using Donchian channel
"""
from vnpy.trader.vtConstant import *
from vnpy.trader.app.ctaStrategy import CtaTemplate
import talib as ta

from datetime import datetime
from DonchianSignal import DonSignal

########################################################################
# 策略继承CtaTemplate
class Donchian_Strategy(CtaTemplate):
    """策略Demo"""
    className = 'DonchianSignal'
    author = 'diwei'
    
    # 策略变量
    transactionPrice = None # 记录成交价格
    
    # 参数列表
    paramList = [
                 # 时间周期
                 'timeframeMap',
                 # 取Bar的长度
                 'barPeriod',
                 # 环境周期
                 'envPeriod',
                 # 信号周期
                 'bandPeriod', 
                 # 出场周期
                 'atrPeriod',
                 # 止损倍数
                 'stopAtrTime',
                 # 交易品种
                 'symbolList',
                 # 交易手数
                 'lot'
                ]    
    
    # 变量列表
    varList = ['transactionPrice']  
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['posDict', 'eveningDict']

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        # 首先找到策略的父类（就是类CtaTemplate），然后把DonchianStrategy的对象转换为类CtaTemplate的对象
        super().__init__(ctaEngine, setting)
        self.paraDict = setting
        self.symbol = self.symbolList[0]

        self.chartLog = {
                'datetime':[],
                'envEMA':[],
                'hhv':[],
                'llv':[]
                }

    def prepare_data(self):
        for timeframe in list(set(self.timeframeMap.values())):
            self.registerOnBar(self.symbol, timeframe, None)

    def arrayPrepared(self, period):
        am = self.getArrayManager(self.symbol, period)
        if not am.inited:
            return False, None
        else:
            return True, am

    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略"""
        self.setArrayManagerSize(self.barPeriod)
        self.prepare_data()
        self.putEvent()

    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'策略启动')
        self.putEvent()
    
    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略"""
        self.writeCtaLog(u'策略停止')
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送"""
        pass
    '''
    def stoploss(self, bar):
        if self.posDict[self.symbol+'_LONG']>0:
            if bar.low<self.transactionPrice*(1-self.stoplossPct):
                self.cancelAll()
                self.sell(self.symbol, bar.close*0.99, self.posDict[self.symbol+'_LONG'])
        if self.posDict[self.symbol+'_SHORT']>0:
            if bar.high>self.transactionPrice*(1+self.stoplossPct):
                self.cancelAll()
                self.cover(self.symbol, bar.close*1.01, self.posDict[self.symbol+'_SHORT'])
    '''
    def strategy(self, bar):
        envPeriod= self.timeframeMap["envPeriod"]
        signalPeriod= self.timeframeMap["signalPeriod"]
        # 根据出场信号出场
        breakBand, hhv, llv, atr = self.exitSignal(signalPeriod)
        exitStatus = self.exitOrder(bar, breakBand, hhv, llv, atr)

        # 根据进场信号进场
        if not exitStatus:
            entrySig = self.entrySignal(envPeriod, signalPeriod)
            self.entryOrder(bar, entrySig)

        # 触发止损
        '''
        if exitStatus == 0:
            self.stoploss(bar)
        '''
    def on5MinBar(self, bar):
        self.strategy(bar)

    def exitSignal(self, signalPeriod):
        arrayPrepared1, amSignal = self.arrayPrepared(signalPeriod)
        if arrayPrepared1:
            algorithm = DonSignal()
            breakBand, hhv, llv = algorithm.breakBand(amSignal, self.paraDict)
            atr = algorithm.atrExit(amSignal, self.paraDict)
        return breakBand, hhv, llv, atr

#edit from here***
    def exitOrder(self, bar, breakBand, hhv, llv, atr):
        exitStatus = 0
        longStop, shortStop = None, None
        if self.transactionPrice:
            longStop = hhv[-1]-self.stopAtrTime*atr[-1]
            shortStop = llv[-1]+self.stopAtrTime*atr[-1]
            # 洗价器
        if (self.posDict[self.symbol+'_LONG'] > 0):
            if (bar.low < longStop):
                # print('LONG stopLoss')
                self.cancelAll()
                self.sell(self.symbol,bar.close*0.99, self.posDict[self.symbol+'_LONG'])
                exitStatus = 1
        elif (self.posDict[self.symbol+'_SHORT'] > 0):
            if (bar.high > shortStop):
                # print('SHORT stopLoss')
                self.cancelAll()
                self.cover(self.symbol,bar.close*1.01, self.posDict[self.symbol+'_SHORT'])
                exitStatus = 1
        return exitStatus

    def entrySignal(self, envPeriod, signalPeriod):
        arrayPrepared1, amEnv = self.arrayPrepared(envPeriod)
        arrayPrepared2, amSignal = self.arrayPrepared(signalPeriod)
        entrySignal = 0
        if arrayPrepared1 and arrayPrepared2:
            algorithm = DonSignal()
            envDirection, envEMA = algorithm.emaEnvironment(amEnv, self.paraDict)
            breakBand, hhv, llv = algorithm.breakBand(amSignal, self.paraDict)
            
            if envDirection==1 and breakBand==1:
                entrySignal = 1
            elif envDirection==-1 and breakBand==-1:
                entrySignal = -1
            else:
                entrySignal = 0

            self.chartLog['datetime'].append(datetime.strptime(amSignal.datetime[-1], "%Y%m%d %H:%M:%S"))
            self.chartLog['envEMA'].append(envEMA[-1])
            self.chartLog['hhv'].append(hhv[-1])
            self.chartLog['llv'].append(llv[-1])
        return entrySignal

    def entryOrder(self, bar, entrySignal):
        # 如果金叉时手头没有多头持仓
        if (entrySignal==1) and (self.posDict[self.symbol+'_LONG']==0):
            # 如果没有空头持仓，则直接做多
            if  self.posDict[self.symbol+'_SHORT']==0:
                self.buy(self.symbol, bar.close*1.01, self.lot)  # 成交价*1.01发送高价位的限价单，以最优市价买入进场
            # 如果有空头持仓，则先平空，再做多
            elif self.posDict[self.symbol+'_SHORT'] > 0:
                self.cancelAll() # 撤销挂单
                self.cover(self.symbol, bar.close*1.01, self.posDict[self.symbol+'_SHORT']) 
                self.buy(self.symbol, bar.close*1.01, self.lot)
        # 如果死叉时手头没有空头持仓
        elif (entrySignal==-1) and (self.posDict[self.symbol+'_SHORT']==0):
            if self.posDict[self.symbol+'_LONG']==0:
                self.short(self.symbol, bar.close*0.99, self.lot) # 成交价*0.99发送低价位的限价单，以最优市价卖出进场
            elif self.posDict[self.symbol+'_LONG'] > 0:
                self.cancelAll() # 撤销挂单
                self.sell(self.symbol, bar.close*0.99, self.posDict[self.symbol+'_LONG'])
                self.short(self.symbol, bar.close*0.99, self.lot)
        # 发出状态更新事件
        self.putEvent()


        # self.entryOrder(maCrossSignal)
    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送"""
        # 对于无需做细粒度委托控制的策略，可以忽略onOrder
        pass
    
    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """收到成交推送"""
        if trade.offset == OFFSET_OPEN:  # 判断成交订单类型
            self.transactionPrice = trade.price # 记录成交价格

    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass