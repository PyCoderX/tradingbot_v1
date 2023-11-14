import datetime
from pathlib import Path

import dill

from src import fyersLogin, telegram


def is_current(fname: Path) -> bool:
    # if file dose not exist, return False
    if not Path.exists(fname):
        return False

    # get today's date
    today = datetime.datetime.now().date()

    # get file modification date
    modification_time = fname.stat().st_mtime
    modification_date = datetime.datetime.fromtimestamp(modification_time).date()

    return modification_date == today


def get_instance(logdir: Path):
    # filenames for telegram Bot and Fyers
    telegramBot_fname = Path.joinpath(logdir, "telegramBot.pickle")
    fyers_fname = Path.joinpath(logdir, "fyers.pickle")

    if not is_current(telegramBot_fname):
        # initiate telegram Bot instance
        telegramBot = telegram.TelegramBot(log_path=logdir)
        with open(telegramBot_fname, "wb") as file:
            dill.dump(telegramBot, file, byref=False, recurse=True)
    else:
        # Export telegramBot
        with open(telegramBot_fname, "rb") as file:
            telegramBot = dill.load(file)

    if not is_current(fyers_fname):
        # initiate fyers login instance
        fyers = fyersLogin.FyersLogin(log_path=logdir, teleBot=telegramBot).__call__()
        with open(fyers_fname, "wb") as file:
            dill.dump(fyers, file, byref=False, recurse=True)
    else:
        # Export fyers instance
        with open(fyers_fname, "rb") as file:
            fyers = dill.load(file)

    return telegramBot, fyers
