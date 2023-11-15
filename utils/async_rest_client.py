import json
import httpx
import asyncio
from functools import wraps


class AsyncRestClient:
    """
    A class for making HTTP requests with error handling and JSON parsing.

    Attributes:
        VALID_METHODS (list): A list of valid HTTP methods supported by this client.
    """

    VALID_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "CONNECT", "TRACE"]

    def __init__(self, timeout=5):
        """
        Initialize the RestClient.

        Args:
            timeout (int, optional): Timeout for HTTP requests in seconds. Defaults to 5 seconds.
        """
        self.timeout = timeout

    def validate_method(self, method):
        """
        Validate that the HTTP method is one of the valid methods.

        Args:
            method (str): The HTTP method to validate.

        Raises:
            ValueError: If the method is not valid.
        """
        if method.upper() not in self.VALID_METHODS:
            raise ValueError(f"Invalid method: {method}")

    def async_run(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            data = asyncio.run(func(*args, **kwargs))
            return data

        return wrapper

    def request(self, func):
        """
        Decorator for making HTTP requests with error handling and JSON parsing.

        Args:
            func (callable): The function to be decorated, representing the HTTP request parameters.

        Returns:
            callable: The decorated function.

        Raises:
            httpx.RequestError: If the HTTP request encounters an exception.
            ValueError: If there is a JSON parsing error in the response.
        """

        @wraps(func)
        async def wrapper(*args, **kwargs):
            input_data = await func(*args, **kwargs)
            method = input_data.get("method", "GET")

            try:
                self.validate_method(method)
                async with httpx.AsyncClient() as client:
                    response = await client.request(timeout=self.timeout, **input_data)
                    response.raise_for_status()  # Raise an HTTPError for bad status codes
                    try:
                        data = response.json()  # Try to parse the response data into a JSON object
                    except json.JSONDecodeError as e:
                        try:
                            data = response.text  # Try to parse the response data into a text object
                        except:
                            raise ValueError(f"Failed to parse response JSON: {str(e)}")
                return data
            except httpx.RequestError as e:
                raise  # Re-raise the original exception

        return wrapper


# Example usage:
if __name__ == "__main__":
    a = AsyncRestClient()

    @a.async_run
    @a.request
    async def get_example_data():
        return {
            "url": "https://pokeapi.co/api/v2/berry/",
            "method": "GET",
            "headers": {"Content-Type": "application/json"},
            "params": {"id": 125},
        }

    data = get_example_data()
    print(data)
