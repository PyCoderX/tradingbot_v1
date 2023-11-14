import time
from functools import wraps


def retry(max_attempts=3, initial_delay=3, backoff_factor=2, do_print: bool = True):
    """
    Retry decorator with exponential backoff on exception.

    Args:
        max_attempts (int, optional): The maximum number of retry attempts (default is 3).
        initial_delay (float, optional): The initial delay in seconds between retries (default is 3).
        backoff_factor (float, optional): The factor by which the delay should lengthen after each failure (default is 2).

    Raises:
        ValueError: If backoff_factor is not greater than 1, max_attempts is negative, or initial_delay is not greater than 0.

    Returns:
        callable: A decorator that can be applied to functions.
    """
    if backoff_factor <= 1:
        raise ValueError("backoff_factor must be greater than 1")

    max_attempts = int(max_attempts)
    if max_attempts < 0:
        raise ValueError("max_attempts must be 0 or greater")

    if initial_delay <= 0:
        raise ValueError("initial_delay must be greater than 0")

    def retry_decorator(func):
        @wraps(func)
        def wrapped_function(*args, **kwargs):
            remaining_attempts, current_delay = max_attempts, initial_delay  # make mutable

            while remaining_attempts > 0:
                try:
                    result = func(*args, **kwargs)  # First attempt
                    return result
                except Exception as error:
                    remaining_attempts -= 1  # Consume an attempt
                    time.sleep(current_delay)  # Wait...
                    current_delay *= backoff_factor  # Make future wait longer
                    if do_print:
                        print(f"Error occurred while executing {func.__name__}. \nRetrying ...")
                    if remaining_attempts <= 0:
                        raise error

            raise Exception(f"Failed to execute {func.__name__} after {max_attempts} attempts. ")

        return wrapped_function

    return retry_decorator
