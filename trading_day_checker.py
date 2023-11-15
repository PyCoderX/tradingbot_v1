import datetime
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

import instances
from nseapi import NSEAPI
from utils import retry


@dataclass
class TradingDayChecker:
    teleBot: Any

    @retry(max_attempts=5, initial_delay=3, backoff_factor=5)
    def __post_init__(self):
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
            self.teleBot.sendMessage(
                "Today is a designated non-trading day. We recommend shutting down the system."
            )
            if sys.platform == "linux":
                time.sleep(120)
                os.system("shutdown -h now")
                time.sleep(120)
