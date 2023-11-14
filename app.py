"""
This the main application for the intraday trading in cash market
@author: Subhajit Bhar
@Created: 5 Oct 2023
@Last updated on 10 Oct 2023
"""

import datetime
import os
import queue
import sys
import threading
import time
from pathlib import Path

import pandas as pd
from httpx import get

import handle_status
import instances
from dataProcessor import DataProcessor
from fyersDataSocket import DataSocket
from nseapi import NSEAPI
from premarket import PreMarketAnalysis

# * global variables
today = datetime.datetime.now().date()
premarket_open_time = datetime.time(9, 0)
market_open_time = datetime.time(9, 15)
market_close_time = datetime.time(15, 30)

# * Set log and data directory

log_dir = Path.joinpath(Path.cwd(), "log")
data_dir = Path.joinpath(Path.cwd(), "data")

for dir in [log_dir, data_dir]:
    Path.mkdir(dir, exist_ok=True)

# * initialize telegram Bot and Fyers API
teleBot, FyersClient = instances.get_instance(logdir=log_dir)

# * initialize NSE API
nse = NSEAPI()

# * get list of holidays from NSE
list_of_holidays = pd.DataFrame.from_records(nse.get_holidays.get("CM"))
off_days = list_of_holidays.tradingDate.to_list()
# print(off_days)


# ? check if today is trading holiday or not
# TODO if today is trading holiday then shutdown the linux system  and quit the program for windows system
# TODO if today is not trading holiday then proceed accordingly

is_offDay: bool = today.strftime("%d-%b-%Y") in off_days or today.weekday() in {5, 6}
if is_offDay:
    teleBot.sendMessage(
        "Today is a designated non-trading day. We recommend shutting down the system."
    )
    if sys.platform == "linux":
        os.system("shutdown -h now")
        time.sleep(10)
    else:
        quit()

else:
    # * get list of ymbols by doing Pre Market Analysis
    fpath = Path.joinpath(Path.cwd(), "data", "SelectedStock.csv")
    if instances.is_current(fpath):
        df = pd.read_csv(fpath, index_col=0)
    else:
        PMA = PreMarketAnalysis(FyersClient)
        df = PMA.get_watchlist(index="nifty 100")
        df.to_csv(fpath)

    symbols_info: dict = df.set_index("Symbol").to_dict(orient="index")
    symbols_to_watch = list(symbols_info.keys())
    print(symbols_to_watch)

    # * get the access token from fyers client
    token = f"{FyersClient.client_id}:{FyersClient.access_token}"

    # * initialize the the DataSocket
    data_queue = queue.Queue()
    ds = DataSocket(access_token=token, symbols=symbols_to_watch, data_queue=data_queue)
    data_thread = threading.Thread(target=ds, daemon=True)
    data_thread.start()

    # * initialize the the DataProcessor
    data_processed_queue = queue.Queue()
    dp = DataProcessor(
        data_queue=data_queue,
        data_forward_queue=data_processed_queue,
        log_path=data_dir,
    )

    data_processor_thread = dp()
    data_processor_thread.start()


while datetime.datetime.now().time() < market_close_time:
    try:
        # * get real_time_data from queue
        real_time_data = data_processed_queue.get(block=False, timeout=1)

        # * convert to datetime objects
        real_time_data["timestamp"] = pd.to_datetime(
            real_time_data["last_traded_time"], unit="s"
        ) + datetime.timedelta(hours=5, minutes=30)

        # * get the date and time separately
        real_time_data["date"] = real_time_data["timestamp"].dt.date
        real_time_data["time"] = real_time_data["timestamp"].dt.time

        # * reset the index to timestamps

        real_time_data.set_index("timestamp", inplace=True)

        # * data filter : data between market hours and  sort by timestamp
        today = datetime.datetime.now().date().strftime("%Y-%m-%d")
        real_time_data = real_time_data.between_time("9:15", "15:30")
        real_time_data = real_time_data.sort_values(by="time")

        # * get the orderbook
        OrderBook = pd.DataFrame.from_records(FyersClient.orderbook)

        for symbol in symbols_to_watch:
            symbol_real_time_data = real_time_data[real_time_data.symbol == symbol].copy()

            #  * convert real time data to ohlc data
            symbol_ohlc = (
                symbol_real_time_data.between_time("9:15", "15:30")
                .resample("5min")["ltp"]
                .ohlc()
            )

            # * get symbol info from symbols_info
            symbol_info = symbols_info.get(symbol, {})

            # * initialize the status variable
            if not symbol_info.get("status"):
                symbol_info = handle_status.initialize(symbol_info, symbol)

            # * check the status of the symbol
            status = symbol_info.get("status")

            # todo 1: if status is onScan: Scan the market and generate Buy Sell signals
            # todo 2: if status is onPositionQ: place the order
            # todo 3: if status is onPosition: Trail the stoploss
            # todo 4: if status is onCancel: Cancel the order (This may be because of wait time limit or max Position limit exceeded)
            # todo 5: if status is onExitQ: Exit the existing order

            match status:
                case "onScan":
                    handle_status.onScan(symbol_info, symbol_ohlc)
                case "onPositionQ":
                    handle_status.onPositionQ(symbol_info, FyersClient)
                case "onPosition":
                    pass
                case "onCancel":
                    pass
                case "onExitQ":
                    pass
                case _:
                    pass

    except:
        pass


"""  
while True:
    try:
        msg = data_queue.get(block=False, timeout=1)
        print(msg)
        msg = data_processed_queue.get(block=False, timeout=1)
        print(msg)
    except queue.Empty:
        # print("queue is empty")
        pass
    except Exception as e:
        print(e)
"""
