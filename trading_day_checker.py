import datetime
import os
import sys
import time
from pathlib import Path

import pandas as pd

import instances
from nseapi import NSEAPI


class TradingDayChecker:
    def __init__(self):
        # * Initialization of telegram bot and Fyers Client
        # * Set log and data directory
        self.log_dir = Path.joinpath(Path.cwd(), "log")
        self.data_dir = Path.joinpath(Path.cwd(), "data")

        for dir in [self.log_dir, self.data_dir]:
            Path.mkdir(dir, exist_ok=True)

        # * Initialize telegram Bot and Fyers API
        teleBot, FyersClient = instances.get_instance(logdir=self.log_dir)

        teleBot.sendMessage(FyersClient.access_token)

        # * Is it a holiday or a weekend?
        today = datetime.datetime.now().date()

        # * Initialize NSE API
        self.nse = NSEAPI()

        # * Get list of holidays from NSE
        list_of_holidays = pd.DataFrame.from_records(self.nse.get_holidays.get("CM"))
        off_days = list_of_holidays.tradingDate.to_list()

        # * Check if today is a trading holiday or not
        is_off_day = today.strftime("%d-%b-%Y") in off_days or today.weekday() in {5, 6}
        if is_off_day:
            teleBot.sendMessage(
                "Today is a designated non-trading day. We recommend shutting down the system."
            )
            if sys.platform == "linux":
                time.sleep(120)
                os.system("shutdown -h now")
                time.sleep(120)
