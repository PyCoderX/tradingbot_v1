from pathlib import Path

import pandas as pd

import instances
from premarket import PreMarketAnalysis
from trading_day_checker import TradingDayChecker

if __name__ == "__main__":
    # * Set log and data directory
    log_dir = Path.joinpath(Path.cwd(), "log")
    data_dir = Path.joinpath(Path.cwd(), "data")

    for dir in [log_dir, data_dir]:
        Path.mkdir(dir, exist_ok=True)

    # * Initialize telegram Bot and Fyers API
    teleBot, FyersClient = instances.get_instance(logdir=log_dir)
    # teleBot.sendMessage(FyersClient.access_token)

    # TradingDayChecker(teleBot=teleBot)

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
