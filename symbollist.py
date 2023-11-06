import utils
import json


class SymbolList:
    def __init__(self, index: str):
        self.index = index

    def getSymbols(self) -> list:
        # common headers
        headers = {"User-Agent": "Mozilla/5.0"}

        # import stock list from nse website
        with open("SectorMap.json", "r") as json_file:
            filenames = json.load(json_file)

        filename = filenames.get(self.index.lower())
        stock_details = utils.read_url(
            url=f"https://www.niftyindices.com/IndexConstituent/{filename}",
            headers=headers,
        )

        # import symbol details from Fyers website
        symbol_details = utils.read_url(
            url="https://public.fyers.in/sym_details/NSE_CM.csv",
            headers=headers,
            columns=(
                "Fytoken",
                "Symbol Details",
                "Exchange Instrument type",
                "Minimum lot size",
                "Tick size",
                "ISIN",
                "Trading Session",
                "Last update date",
                "Expiry date",
                "Symbol",
                "Exchange",
                "Segment",
                "Scrip code",
                "Underlying scrip code",
                "Strike price",
                "Option type",
                "Underlying FyToken",
                "Fytoken1",
                "NA",
            ),
        )

        #  filters for specific scrip codes
        return symbol_details[
            symbol_details.ISIN.isin(stock_details["ISIN Code"].to_list())
        ].Symbol.to_list()

    def __call__(self):
        return self.getSymbols()
