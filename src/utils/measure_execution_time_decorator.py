import time
from functools import wraps
import numpy as np


def MeasureExecutionTime(repeat: int = 1):
    """
    A decorator to measure the execution time of a function.

    Args:
        repeat (int): Number of times to repeat the measurement.

    Returns:
        float: The mean and standard deviation of execution time.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            total_times = []
            for _ in range(repeat):
                start_time = time.perf_counter()
                result = func(*args, **kwargs)
                end_time = time.perf_counter()
                total_times.append(round(end_time - start_time, 2))

            mean_time = np.mean(total_times)
            std_deviation = np.std(total_times)
            print(f"Mean time: {mean_time:.2f} ± {std_deviation:.2f} seconds")
            return result

        return wrapper

    return decorator
