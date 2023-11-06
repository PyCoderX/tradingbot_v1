from technicalanalysis import TechnicalAnalysis
from symbollist import SymbolList
import datetime
import pandas as pd


class PreMarketAnalysis(TechnicalAnalysis):
    def __init__(self, FyersClient, index: str):
        TechnicalAnalysis.__init__(self)
        self.FyersClient = FyersClient
        self.index = index

        funds = self.FyersClient.funds.get("fund_limit")
        self.cash = next(
            elem.get("equityAmount")
            for elem in funds
            if elem.get("title") == "Total Balance"
        )

    @property
    def _getSymbols(self):
        return SymbolList(index=self.index).__call__()

    def _historicalData(self):
        # get symbol list
        symbol_list = self._getSymbols

        # Calculate date range for historical data
        end_date = datetime.datetime.now() + datetime.timedelta(days=-1)
        start_date = end_date + datetime.timedelta(days=-100)

        data = {
            "range_to": end_date.date(),
            "range_from": start_date.date(),
            "resolution": "D",
        }
        input_data = [data | {"symbol": symbol} for symbol in symbol_list]
        del data
        return [self.FyersClient.history_daily(data) for data in input_data]

    def get_watchlist(self):
        hist_data = self._historicalData()
        symbol_pivot = [
            self.calculate_fibonacci_pivots(data, self.cash) for data in hist_data
        ]
        df = pd.DataFrame.from_records(symbol_pivot)
        return df[df["RB_Candidate"]]
