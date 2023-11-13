import datetime
from pathlib import Path

import pandas as pd

import instances
from utils import rest_client

client = rest_client.RestClient()


@client.request
def get_value_curve(from_date, to_date, FyersClient):
    return {
        "url": "https://api-a1-prod.fyers.in/myaccount-server/v1/value-curve",
        "params": {
            "from_date": from_date,
            "to_date": to_date,
        },
        "method": "GET",
        "headers": {"Access-Token": FyersClient.access_token},
    }


def copy_value_curve(FyersClient):
    today = datetime.datetime.now().date() - datetime.timedelta(days=1)
    value_curve = get_value_curve(today, today, FyersClient)
    value_curve["response"]
    columns = [
        elem.replace("_", " ").title()
        for elem in value_curve["response"].get("values_indexes")
    ]
    value_curve = pd.DataFrame(value_curve["response"].get("records"), columns=columns)
    value_curve = value_curve.reindex(
        columns=[
            "Trade Date",
            "Cd Position Value",
            "Holding Value",
            "T1 Holding Value",
            "Mf Value",
            "Fo Position Value",
            "Mcx Position Value",
            "Fund Value",
            "Total Value",
        ]
    )
    value_curve["Trade Date"] = pd.to_datetime(
        value_curve["Trade Date"], format="%Y-%m-%d"  # type: ignore
    )
    value_curve = value_curve.set_index("Trade Date")
    del value_curve["Total Value"]
    return value_curve.to_clipboard(header=None)


if __name__ == "__main__":
    # * Set log and data directory

    log_dir = Path.joinpath(Path.cwd(), "log")
    data_dir = Path.joinpath(Path.cwd(), "data")

    for dir in [log_dir, data_dir]:
        Path.mkdir(dir, exist_ok=True)

    teleBot, FyersClient = instances.get_instance(logdir=log_dir)
    # * get the value curve and copy to clipboard
    copy_value_curve(FyersClient)
