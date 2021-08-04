# IMPORTS
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

# FROM IMPORTS
from pathlib import Path
from scipy.optimize import brute

# Ignore Warnings - Not recommended, but looks nice.
import warnings
warnings.filterwarnings("ignore")

class SMABackTest(object):

    def __init__(self, ticker: str, short_window=30, long_window=50, period="ytd", interval="1h"):
        
        """
        Class for backtesting of SMA-based trading strategies.
        
        :Attributes:
        ============
            ticker : str
                Valid tickers: Anything found on YFinance or American stock exchanges
                Examples: TSLA, NIO, F
            short_window : int
                Valid window: Anything less than the long window.
            long_window : int
                Valid window: Anything greater than the short window.
            period : str
                Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
            interval : str
                Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
            share size : int
                Default: 50
            initial capital : int
                Default: $10,000 (10000)
        """
    
        self.ticker = ticker
        self.short_window = short_window
        self.long_window = long_window
        self.period = period
        self.interval = interval
        self.share_size = 50
        self.initial_capital = 10000
        self.getDataFrame()

    def getDataFrame(self):
        
        """
        Creates a DataFrame of the asset with a short SMA, long SMA,
            cross over signals, and whether to enter or exit a trade.
            
        :Parameters:
        ============
            short_window : int
                Valid input: ints less than the size of the long_window
            long_window : int
                Valid input: ints greater than the size of the short_window
        """
        
        # Building DataFrame
        
        df = yf.Ticker(self.ticker).history(period=self.period, interval=self.interval)
        df['Return'] = np.log(df["Close"] / df["Close"].shift(1))
        df[f"SMA{self.short_window}"] = df["Close"].rolling(window=self.short_window).mean()
        df[f"SMA{self.long_window}"] = df["Close"].rolling(window=self.long_window).mean()
        df["Signal"] = 0.0
        
        # Clean DataFrame
        
        df.drop(columns=["Dividends","Stock Splits"], inplace=True)
        
        # Establish DataFrame as property
        
        self.df = df
        
    def runStrategy(self):
        
        """
         Backtests trading strategy
        """

        # DATA
        df = self.df.copy().dropna()
        
        # POSITION, 1 LONG, -1 SHORT
        df['Position'] = np.where(
            df[f"SMA{self.short_window}"] > df[f"SMA{self.long_window}"],
            1,
            -1
        )
        
        # SIGNAL TO ACTION, 1 for LONG ORDER, -1 SHORT ORDER
        df['Signal'] = df['Position'][df['Position'].diff() != 0]
        
        # RETURNS
        df['Strategy Returns'] = df['Position'].shift(1) * \
            df['Return']
        df['Cumulative Returns'] = self.initial_capital * \
            df['Return'].cumsum().apply(np.exp)
        df['Cumulative Strat Returns'] = self.initial_capital * \
            df['Strategy Returns'].cumsum().apply(np.exp)
        df['Signal'].fillna(0, inplace=True)
        
        # Drop first row of NaN data
        df.dropna(inplace=True)
        
        # results returns data DF
        self.results = df
        
        # Gross / Actual Performance
        stratPerformance = df['Cumulative Strat Returns'].iloc[-1]
        
        # Buy & Hold (Cumulative Returns)
        buyAndHold = df['Cumulative Returns'].iloc[-1]
        
        # Over or Under perform?
        stratDifference = stratPerformance - buyAndHold
        
        # Print Strat/BuyHold/Dif Results
        #print(f"Strategy: {round(stratPerformance, 2)}.\nBuy and Hold: {round(buyAndHold, 2)}\nDifference: {round(stratDifference, 2)}")
        
        return round(stratPerformance, 2), round(stratDifference, 2)
        

    def plotReturns(self):
        
        """
         Plots the cumulative returns of the strategy vs buying and holding.
        """
        
        if self.results is None:
            print('No results to plot yet. Run a strategy.')
        
        title = "%s | Short SMA=%d, Long SMA=%d" % (self.ticker,
                                           self.short_window,
                                           self.long_window)
        self.results[["Cumulative Returns","Cumulative Strat Returns"]]\
            .plot(title=title,figsize=(10, 6))
        
    def plotCrossover(self):
        
        """
         Plots the short and long SMA windows next to the price of the asset.
        """
        
        if self.df is None:
            print("There is no data to plot. Run a strategy.")
            
        title = "%s | Short SMA=%d, Long SMA=%d" % (self.ticker,
                                                    self.short_window,
                                                   self.long_window)
        
        self.df[["Close",f"SMA{self.short_window}",f"SMA{self.long_window}"]]\
            .plot(title=title, figsize=(10,6))
        
    def evaluatePortfolio(self):
        
        """
         Shows important financial ratios of asset
        """
        
        if self.results is None:
            print("There are no results to evaluate. Run a strategy.")
            
        df = self.results
        
        # Portfolio Evaluation

        # Prepare DataFrame for metrics
        metrics = [
            'Annual Return',
            'Cumulative Returns',
            'Annual Volatility',
            'Sharpe Ratio',
            'Sortino Ratio']
        columns = ['Backtest']

        # Initialize the DataFrame with index set to evaluation metrics and column as `Backtest` (just like PyFolio)
        portfolio_evaluation_df = pd.DataFrame(index=metrics, columns=columns)

        # Calculate cumulative return
        portfolio_evaluation_df.loc['Cumulative Returns'] = df["Cumulative Strat Returns"][-1]

        # Calculate annualized return
        portfolio_evaluation_df.loc['Annual Return'] = (df['Strategy Returns'].mean() * 252)

        # Calculate annual volatility
        portfolio_evaluation_df.loc['Annual Volatility'] = (df['Return'].std() * np.sqrt(252))

        # Calculate Sharpe Ratio
        portfolio_evaluation_df.loc['Sharpe Ratio'] = (df['Strategy Returns'].mean() * 252) / (df['Strategy Returns'].std() * np.sqrt(252))

        # Calculate Downside Return
        sortino_ratio_df = df[['Strategy Returns']].copy()
        sortino_ratio_df.loc[:,'Downside Returns'] = 0
        target = 0
        mask = sortino_ratio_df['Strategy Returns'] < target
        sortino_ratio_df.loc[mask, 'Downside Returns'] = sortino_ratio_df['Strategy Returns']**2


        # Calculate Sortino Ratio
        down_stdev = np.sqrt(sortino_ratio_df['Downside Returns'].mean()) * np.sqrt(252)
        expected_return = sortino_ratio_df['Strategy Returns'].mean() * 252
        sortino_ratio = expected_return/down_stdev
        portfolio_evaluation_df.loc['Sortino Ratio'] = sortino_ratio
        
        self.portfolioEvaluationDF = portfolio_evaluation_df
        
    def set_parameters(self, short_window=None, long_window=None):
        """
         Sets parameters of SMA strategy
        """
        
        if short_window is not None:
            self.short_window = short_window
            self.df[f"SMA{self.short_window}"] = self.df["Close"]\
                                                     .rolling(window=self.short_window)\
                                                     .mean()
        if long_window is not None:
            self.long_window = long_window
            self.df[f"SMA{self.long_window}"] = self.df["Close"]\
                                                    .rolling(window=self.long_window)\
                                                    .mean()
            
    def update_and_run(self, SMA):
        """
         Update the parameters of the strategy and run
        """
        self.set_parameters(int(SMA[0]), int(SMA[1]))
        return -self.runStrategy()[0]
    
    def optimize_parameters(self, short_range, long_range):
        """
         Brute force optimization, using SciKit Learn
        """
        
        opt = brute(self.update_and_run, (short_range, long_range), finish=None)
        return opt, -self.update_and_run(opt)
    
if __name__ == '__main__':
    ups = SMABackTest(ticker="UPS")
    print(f"Running SMA Backtest for {ups.ticker}.")
    print(f"The original strategy of SMA{ups.short_window} & SMA{ups.long_window} returns: {ups.runStrategy()}")
    print(f"Optimizing...")
    print(f"The best windows with the best return is: {ups.optimize_parameters((20, 60, 1), (20, 110, 1))}")