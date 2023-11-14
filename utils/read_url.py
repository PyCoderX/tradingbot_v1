import io
import pandas as pd
import requests
from functools import lru_cache
import utils


@utils.freezeargs
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
