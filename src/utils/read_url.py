import io
from functools import lru_cache, wraps

import pandas as pd
import requests
from frozendict import frozendict


def freezeargs(func):
    """
    Transform mutable dictionnary  Into immutable
    Useful to be compatible with cache
    """

    @wraps(func)
    def wrapped(*args, **kwargs):
        args = tuple(frozendict(arg) if isinstance(arg, dict) else arg for arg in args)
        kwargs = {
            k: frozendict(v) if isinstance(v, dict) else v for k, v in kwargs.items()
        }
        return func(*args, **kwargs)

    return wrapped


@freezeargs
@lru_cache(maxsize=10)
def read_url(url, headers=None, columns=None):
    """
    Fetches data from a URL and returns the response content as JSON.

    Args:
        url (str): The URL to fetch data from.
        headers (dict, optional): Headers to include in the HTTP request (default is None).
        columns (list, optional): List of column names for the DataFrame (default is None).

    Returns:
        pd.DataFrame: The DataFrame containing the data from the CSV response, or None if the request fails or parsing fails.
    """
    try:
        # Send an HTTP GET request to the URL with optional headers
        response = requests.get(url, headers=headers)

        # Raise an HTTPError for bad status codes
        response.raise_for_status()

        return pd.read_csv(io.StringIO(response.text), names=columns)
    except requests.exceptions.RequestException as e:
        raise e  # Re-raise the original exception
