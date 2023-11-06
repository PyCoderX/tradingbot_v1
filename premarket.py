from technicalanalysis import TechnicalAnalysis
from symbollist import SymbolList
import datetime
import pandas as pd


class PreMarketAnalysis(TechnicalAnalysis):
    def __init__(self, FyersClient):
        TechnicalAnalysis.__init__(self)
        self.FyersClient = FyersClient

        funds = self.FyersClient.funds.get("fund_limit")
        self.cash = next(
            elem.get("equityAmount")
            for elem in funds
            if elem.get("title") == "Total Balance"
        )

    def _getSymbols(self, index: str) -> list:
        return SymbolList(index=index).__call__()

    def _historicalData(self, index: str):
        # get symbol list
        symbol_list = self._getSymbols(index)

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

    def get_watchlist(self, index: str):
        hist_data = self._historicalData(index)
        symbol_pivot = [
            self.calculate_fibonacci_pivots(data, self.cash) for data in hist_data
        ]
        df = pd.DataFrame.from_records(symbol_pivot)
        return df[df["RB_Candidate"]]
