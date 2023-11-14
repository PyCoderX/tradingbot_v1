import datetime
import pandas as pd
import requests


def initialize(symbol_info: dict, symbol: str, cash: float | int = 5000):
    symbol_info["status"] = "onScan"
    symbol_info["symbol"] = symbol
    symbol_info["range"] = 1.2 * (symbol_info["PDH"] - symbol_info["PDL"])
    symbol_info["quantity"] = int(0.01 * cash / symbol_info["range"])
    return symbol_info


def onScan(symbol_info: dict, symbol_ohlc: pd.DataFrame) -> dict:
    # * get last three close value
    previousClose, close, _ = symbol_ohlc.tail(3).close.to_list()

    if previousClose <= symbol_info["PDH"] and close > symbol_info["PDH"]:
        symbol_info["status"] = "onPositionQ"
        symbol_info["side"] = 1

    elif previousClose >= symbol_info["PDL"] and close < symbol_info["PDL"]:
        symbol_info["status"] = "onPositionQ"
        symbol_info["side"] = -1

    return symbol_info


def onPositionQ(symbol_info: dict, FyersClient) -> dict:
    price = (
        symbol_info.get("PDH") if symbol_info.get("side") == 1 else symbol_info.get("PDL")
    )
    data = {
        "symbol": symbol_info.get("symbol"),
        "qty": symbol_info.get("quantity", 0),
        "type": 1,
        "side": symbol_info.get("side"),
        "productType": "BO",
        "validity": "DAY",
        "disclosedQty": 0,
        "offlineOrder": "False",
        "limitPrice": price,
        "stopPrice": 0,
        "stopLoss": symbol_info.get("range"),
        "takeProfit": 1.5 * symbol_info["range"],
    }
    try:
        response = FyersClient.place_order(data=data)
        symbol_info["orderID"] = response["id"]
        symbol_info["orderTime"] = datetime.datetime.now()
        symbol_info["waitTime"] = datetime.datetime.now() + datetime.timedelta(minutes=30)
        symbol_info["status"] = "onPosition"
        symbol_info["SL_level"] = price - data.get("side", 1) * data.get("stopLoss")
        print(
            f"Placed order for {symbol_info.get('symbol')}. Side: {'Buy' if symbol_info.get('side') == 1 else 'Sell'}, Price: {price}, SL: {symbol_info.get('range')}, Qunatity: {symbol_info['quantity']}"
        )
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
    except Exception as e:
        pass
    finally:
        return symbol_info


def onPosition(symbol_info: dict, symbol_ohlc: pd.DataFrame) -> dict:
    #  monitor the existifng open positions

    return symbol_info


def onCancel(symbol_info: dict) -> dict:
    #  do something
    return symbol_info


def onExitQ(symbol_info: dict) -> dict:
    #  do something
    return symbol_info
