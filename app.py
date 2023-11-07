""" 
This the main application for the intraday trading in cash market
@author: Subhajit Bhar
@Created: 5 Oct 2023
@Last updated on 6 Oct 2023
"""


import datetime
import os
from pathlib import Path
import sys
import time
from nseapi import NSEAPI
import pandas as pd
import instances

from premarket import PreMarketAnalysis
from fyersDataSocket import DataSocket
from dataProcessor import DataProcessor

import queue
import threading

# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# initiate telegram and FyersClient
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# Set log and data directory

log_dir = Path.joinpath(Path.cwd(), "log")
data_dir = Path.joinpath(Path.cwd(), "data")

for dir in [log_dir, data_dir]:
    Path.mkdir(dir, exist_ok=True)

teleBot, FyersClient = instances.get_instance(logdir=log_dir)


# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# get NSE holiday list
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

nse = NSEAPI()
list_of_holidays = pd.DataFrame.from_records(nse.get_holidays.get("CM"))
off_days = list_of_holidays.tradingDate.to_list()
# print(off_days)

# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# Check if today is a non-trading day
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

today = datetime.datetime.now().date()
is_offDay: bool = today.strftime("%d-%b-%Y") in off_days or today.weekday() in {5, 6}
if is_offDay:
    teleBot.sendMessage(
        "Today is a designated non-trading day. We recommend shutting down the system."
    )
    if sys.platform == "linux":
        os.system("shutdown -h now")
        time.sleep(10)

else:
    PMA = PreMarketAnalysis(FyersClient)
    df = PMA.get_watchlist(index="nifty 100")
    symbol_info = df.set_index("Symbol").to_dict(orient="index")

    symbols_to_watch = list(symbol_info.keys())
    # symbols_to_watch

    token = f"{FyersClient.client_id}:{FyersClient.access_token}"
    data_queue = queue.Queue()
    ds = DataSocket(access_token=token, symbols=symbols_to_watch, data_queue=data_queue)
    data_thread = threading.Thread(target=ds, daemon=True)
    data_thread.start()

    data_processed_queue = queue.Queue()
    dp = DataProcessor(
        data_queue=data_queue, data_forward_queue=data_processed_queue, log_path=log_dir
    )

    data_processor_thread = dp()
    data_processor_thread.start()

    while True:
        try:
            msg = data_queue.get()
            print(msg)
        except queue.Empty:
            pass
        except Exception as e:
            print(e)
