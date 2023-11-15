import utils as utils

client = utils.RestClient()


class NSEAPI:
    def __init__(self):
        self.header = {"User-Agent": "Mozilla/5.0"}

        # API server
        self.nse_API = "https://www.nseindia.com/api"

        # ENDPoints
        self.holidays = "/holiday-master"

    @property
    @client.request
    def get_holidays(self):
        """
        Get the list of holidays from NSE.

        Returns:
            dict: A dictionary containing the holiday details.
        """

        return {
            "method": "GET",
            "url": f"{self.nse_API}{self.holidays}",
            "headers": self.header,
            "params": {"type": "trading"},
        }
