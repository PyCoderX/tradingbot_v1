import datetime
import json
import queue
import threading
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

import instances
from fyersDataSocket import DataSocket
from premarket import PreMarketAnalysis
from trading_day_checker import TradingDayChecker

warnings.filterwarnings("ignore")


def get_data(fname):
    dataframe = pd.read_csv(fname, sep=" ", header=None)
    dataframe = dataframe.drop_duplicates(keep="first")
    header = dataframe.iloc[0]  # grab the first row for the header
    dataframe = dataframe[1:]  # take the data less the header row
    dataframe.columns = header  # set the header row as the df header
    dataframe["timestamp"] = pd.to_datetime(
        dataframe["last_traded_time"], unit="s"
    ) + datetime.timedelta(hours=5, minutes=30)
    dataframe["time"] = dataframe["timestamp"].dt.time
    dataframe = dataframe.set_index("timestamp")
    dataframe["ltp"] = dataframe["ltp"].astype(float)
    return dataframe


round_tick = lambda x: round((x // 0.05 + 1) * 0.05, 2)


def place_order(stock, side, price, sl_level, cash, fc):
    data = {
        "symbol": stock,
        "qty": int(0.01 * cash / sl_level),
        "type": 1,
        "side": side,
        "productType": "BO",
        "validity": "DAY",
        "disclosedQty": 0,
        "offlineOrder": False,
        "limitPrice": price,
        "stopPrice": 0,
        "stopLoss": sl_level,
        "takeProfit": round_tick(1.5 * sl_level),
    }
    print(json.dumps(data, indent=4, default=str))
    response = fc.place_order(data=data)
    teleBot.sendMessage("from local\n"+
        f"Placed order for {stock}. Side: {'Buy' if side == 1 else 'Sell'}, Price: {price}, SL: {sl_level}, Qunatity: {data['qty']}"
    )
    return response


if __name__ == "__main__":
    # * global variables
    today = datetime.datetime.now().date()
    premarket_open_time = datetime.time(9, 0)
    market_open_time = datetime.time(9, 15)
    market_close_time = datetime.time(15, 30)
    current_time = lambda: datetime.datetime.now().time()

    # * Set log and data directory
    log_dir = Path.joinpath(Path.cwd(), "log")
    data_dir = Path.joinpath(Path.cwd(), "data")

    for dir in [log_dir, data_dir]:
        Path.mkdir(dir, exist_ok=True)

    # * Initialize telegram Bot and Fyers API
    teleBot, FyersClient = instances.get_instance(logdir=log_dir)
    teleBot.sendMessage("from local\n"+FyersClient.access_token)

    """ Holiday Checkout"""
    # TradingDayChecker(teleBot=teleBot)

    """ Pre Market Analysis """
    # * get list of ymbols by doing Pre Market Analysis
    fpath = Path.joinpath(Path.cwd(), "data", "SelectedStock.csv")
    if instances.is_current(fpath):
        df = pd.read_csv(fpath, index_col=0)
    else:
        PMA = PreMarketAnalysis(FyersClient)
        df = PMA.get_watchlist(index="nifty 200")
        df.to_csv(fpath)

    symbols_info: dict = df.set_index("Symbol").to_dict(orient="index")
    symbols_to_watch = list(symbols_info.keys())
    print(symbols_to_watch)

    """ Market Analysis"""

    # * Retrieve fund information and calculate available balance
    fund_info = FyersClient.funds["fund_limit"]
    # print(json.dumps(fund_info, indent=4, default=str))
    available_balance = next(
        elem.get("equityAmount") for elem in fund_info if elem["title"] == "Total Balance"
    )
    round_offFactor = 5 * 10 ** (int(np.log10(available_balance)) - 2)
    available_cash = available_balance // round_offFactor * round_offFactor

    # * limit the watchlist to 25
    if len(symbols_to_watch) > 25:
        symbols_to_watch = symbols_to_watch[:25]

    # * get the access token from fyers client
    token = f"{FyersClient.client_id}:{FyersClient.access_token}"

    # * initialize the the DataSocket
    data_queue = queue.Queue()
    fname = Path.joinpath(Path.cwd(), "data", f"{datetime.datetime.today():%d-%b-%Y}.txt")
    ds = DataSocket(
        access_token=token,
        symbols=symbols_to_watch,
        filename=fname,
        data_queue=data_queue,
    )
    data_thread = threading.Thread(target=ds, daemon=True)
    data_thread.start()
    open_position = []
    stock_list = [x for x in symbols_to_watch if x not in open_position]
    master_dict = symbols_info

    while datetime.datetime.now().time() < market_close_time:
        try:
            dataframe = get_data(fname)
            for stock in stock_list:
                stock_data = (
                    dataframe[dataframe.symbol == stock]
                    .between_time("9:15", "15:30")
                    .resample("2min")["ltp"]
                    .ohlc()
                )
                lastClose = stock_data.close.values[-2]
                secondlastClose = stock_data.close.values[-3]
                response = None

                if all(
                    [
                        lastClose > master_dict[stock]["PDH"],
                        secondlastClose < master_dict[stock]["PDH"],
                    ]
                ):
                    master_dict[stock]["sl_level"] = round_tick(
                        master_dict[stock]["PDH"] - master_dict[stock]["PDL"]
                    )
                    if len(open_position) < 5:
                        response = place_order(
                            stock,
                            1,
                            round_tick(master_dict[stock]["PDH"]),
                            master_dict[stock]["sl_level"],
                            available_cash,
                            FyersClient,
                        )

                elif all(
                    [
                        lastClose < master_dict[stock]["PDL"],
                        secondlastClose > master_dict[stock]["PDL"],
                    ]
                ):
                    master_dict[stock]["sl_level"] = round_tick(
                        master_dict[stock]["PDH"] - master_dict[stock]["PDL"]
                    )
                    if len(open_position) < 5:
                        response = place_order(
                            stock,
                            -1,
                            round_tick(master_dict[stock]["PDL"]),
                            master_dict[stock]["sl_level"],
                            available_cash,
                            FyersClient,
                        )

                if response:
                    teleBot.sendMessage("from local\n"+response["message"])
                    if response["s"] == "ok":
                        master_dict[stock]["orderID"] = response["id"]
                        open_position.append(stock)
                        stock_list.remove(stock)
                        teleBot.sendMessage("from local\n"+f"Added {stock} to open positions.")
                    if "Allowed Basket" in response["message"]:
                        stock_list.remove(stock)
                        teleBot.sendMessage("from local\n"+
                            f"Removed {stock} from the stock list due to basket restrictions."
                        )
                    elif "RED:Margin Shortfall" in response["message"]:
                        stock_list.remove(stock)
                        teleBot.sendMessage("from local\n"+
                            f"Removed {stock} from the stock list due to Margin Shortfall."
                        )

            for stock in open_position:
                time.sleep(10)
                try:
                    dataframe = get_data(fname)
                    stock_data = (
                        dataframe[dataframe.symbol == stock]
                        .between_time("9:15", "15:30")
                        .resample("5min")["ltp"]
                        .ohlc()
                    )
                    orderbook = FyersClient.orderbook
                    orderBookDataFrame = pd.DataFrame.from_records(orderbook["orderBook"])
                    orderBookDataFrame = orderBookDataFrame[
                        ~orderBookDataFrame.status.isin([1, 5])
                    ]
                    orderBookDataFrame["orderTime"] = pd.to_datetime(
                        orderBookDataFrame["orderDateTime"], format="%d-%b-%Y %H:%M:%S"
                    )
                    orderBookDataFrame["offloadTime"] = orderBookDataFrame[
                        "orderTime"
                    ] + datetime.timedelta(minutes=30)
                    isinOrderBook = stock in orderBookDataFrame.symbol.values
                    stock_orderBook = orderBookDataFrame[
                        orderBookDataFrame.symbol == stock
                    ]

                    if isinOrderBook:
                        BOstatus = stock_orderBook[
                            stock_orderBook.id == master_dict[stock]["orderID"]
                        ].status.values[0]
                        isWaitTimePassed = (
                            stock_orderBook[
                                stock_orderBook.id == master_dict[stock]["orderID"]
                            ].offloadTime.dt.time.values[0]
                            < current_time()
                        )

                        if BOstatus == 6:
                            if isWaitTimePassed:
                                response = FyersClient.cancel_order(
                                    data={"id": master_dict[stock]["orderID"]}
                                )
                                teleBot.sendMessage("from local\n"+response)
                                open_position.remove(stock)
                                stock_list.append(stock)
                                teleBot.sendMessage("from local\n"+
                                    f"Canceled order for {stock} due to wait time expiration."
                                )
                                teleBot.sendMessage("from local\n"+
                                    f"Removed {stock} from open positions."
                                )
                        elif BOstatus == 2:
                            sl_orderBook = stock_orderBook[stock_orderBook.type == 4]
                            if len(sl_orderBook) > 0:
                                orderId = sl_orderBook["id"].values[0]
                                side = sl_orderBook["side"].values[0]
                                buffer = master_dict[stock]["range"] / 5

                                if isWaitTimePassed:
                                    print(len(stock_data))
                                    if side == -1:
                                        if len(stock_data) > 12:
                                            modified_SL = max(
                                                round_tick(
                                                    stock_data.tail(12).low.min() - buffer
                                                ),
                                                sl_orderBook["stopPrice"].values[0],
                                            )
                                        else:
                                            modified_SL = round_tick(
                                                master_dict[stock]["PDL"] - buffer
                                            )
                                    else:
                                        if len(stock_data) > 12:
                                            modified_SL = min(
                                                round_tick(
                                                    stock_data.tail(12).high.max()
                                                    + buffer
                                                ),
                                                sl_orderBook["stopPrice"].values[0],
                                            )
                                        else:
                                            modified_SL = round_tick(
                                                master_dict[stock]["PDH"] + buffer
                                            )
                                else:
                                    if side == -1:
                                        modified_SL = round_tick(
                                            master_dict[stock]["PDL"] - buffer
                                        )
                                    else:
                                        modified_SL = round_tick(
                                            master_dict[stock]["PDH"] + buffer
                                        )

                                data = {
                                    "id": orderId,
                                    "qty": int(sl_orderBook["qty"].values[0]),
                                    "type": 4,
                                    "side": int(side),
                                    "productType": "BO",
                                    "validity": "DAY",
                                    "disclosedQty": 0,
                                    "offlineOrder": "False",
                                    "stopPrice": float(modified_SL),
                                    "limitPrice": float(modified_SL) + int(side) * 0.0025,
                                }
                                if modified_SL != sl_orderBook["stopPrice"].values[0]:
                                    response = FyersClient.modify_order(data=data)
                                    teleBot.sendMessage("from local\n"+
                                        f"Modified SL for {stock} order. New SL: {modified_SL}, Order ID: {orderId}"
                                    )
                except Exception as e:
                    teleBot.sendMessage("from local\n"+f"Error occurred for {stock} order:\n{e}")

        except queue.Empty:
            pass
        except Exception as e:
            raise e
