import pandas as pd
import numpy as np
import hvplot.pandas
from pathlib import Path

class Asset(object):

    def __init__(self, file: str, short_window: float, long_window: float, initial_capital: float, shares: float):
    
        self.file = file
        self.short_window = short_window
        self.long_window = long_window
        self.initial_capital = initial_capital
        self.shares = shares

    def algoDataFrame(self):
        """
        Creates a DataFrame with 
        """
        # Take in File
        ticker = self.file.split(".")[0]
    
        is_csv = Path(str(self.file)).suffix == ".csv"
    
        if is_csv == True:
            df = pd.read_csv(self.file, parse_dates=True, infer_datetime_format=True)
            df.columns = map(str.lower, df.columns)
        
            signals_df=df.loc[:, ["date", "close"]].copy()
        else:
            ticker = self.file["ticker"][0]
            signals_df=self.file.loc[:,["date","close"]].copy()

        ### Parse through file & create columns

        signals_df = signals_df.set_index("date", drop = True)
        signals_df[f"SMA{self.short_window}"] = signals_df["close"].rolling(window=self.short_window).mean()
        signals_df[f"SMA{self.long_window}"] = signals_df["close"].rolling(window=self.long_window).mean()
        signals_df["Signal"] = 0.0

        # for short
        # When SMA_short < SMA_long, 0
        # when SMA_short > SMA_long, 1
        
        
        # for long 
        # When SMA_short > SMA_long, 0
        # when SMA_short < SMA_long, 1

        signals_df["Signal"][self.short_window:] = np.where(
            signals_df[f"SMA{self.short_window}"][self.short_window:] < signals_df[f"SMA{self.long_window}"][self.short_window:], 1, 0)
        signals_df["Entry/Exit"] = signals_df["Signal"].diff()

        signals_df

    def algoPlot(self):
        """Plots entry & exit points of SMA trading strategy"""
        pass

    def algoRatios(self):
        """Shows important financial ratios of asset"""
        pass

    def algoBackTest(self):
        """Shows backtesting information on asset and SMA trading strategy"""
        pass






