from technicalanalysis import TechnicalAnalysis
from symbollist import SymbolList
import datetime
import pandas as pd
import concurrent.futures


class PreMarketAnalysis(TechnicalAnalysis):
    def __init__(self, FyersClient):
        """Initialize the PreMarketAnalysis object.

        Args:
            FyersClient: The FyersClient object used for accessing Fyers API.

        """
        TechnicalAnalysis.__init__(self)
        self.FyersClient = FyersClient

        funds = self.FyersClient.funds.get("fund_limit")
        self.cash = next(
            elem.get("equityAmount")
            for elem in funds
            if elem.get("title") == "Total Balance"
        )

    def _getSymbols(self, index: str) -> list:
        """Get the list of symbols for the given index.

        Args:
            index: The index for which to retrieve the symbols.

        Returns:
            list: The list of symbols.

        """
        return SymbolList(index=index).__call__()

    def _historicalData(self, index: str):
        """Retrieve historical data for the given index.

        Args:
            index: The index for which to retrieve the historical data.

        Returns:
            list: The historical data for each symbol.

        """
        symbol_list = self._getSymbols(index)

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
        """Get the watchlist for the given index.

        Args:
            index: The index for which to retrieve the watchlist.

        Returns:
            pandas.DataFrame: The watchlist containing symbol pivot data.

        """
        hist_data = self._historicalData(index)
        symbol_pivot = [
            self.calculate_fibonacci_pivots(data, self.cash) for data in hist_data
        ]
        df = pd.DataFrame.from_records(symbol_pivot)
        return df[df["RB_Candidate"]]
