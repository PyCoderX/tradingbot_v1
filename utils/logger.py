import logging
import os
import datetime
import threading
import traceback
from logging.handlers import RotatingFileHandler
from typing import Optional

class ExceptionLogger:
    """
    A utility class that provides a way to log exceptions in Python code.

    Attributes:
        VALID_LOG_LEVELS (set): A set containing the valid log levels.

    Methods:
        __init__(self, logger_name=None, level='INFO', root='root'): Initializes an instance of ExceptionLogger.
        set_logger(self, logger_name, level, root): Sets the logger with the specified name, log level, and root directory.
        setup_logger(self, logger_name, level, root): Configures the logger with the specified name, log level, and root directory.
        log_exception(self, func): Decorator method that logs exceptions raised in the decorated function with the logger.
    """

    VALID_LOG_LEVELS = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}

    def __init__(self, logger_name: Optional[str] =None, level:str ='INFO', log_path:str ='log', reraise_on_exception:bool =False):
        """
        Initializes an instance of ExceptionLogger.

        Args:
            logger_name (str, optional): The name of the logger. If not provided, a default logger name is used.
            level (str, optional): The log level. Defaults to 'INFO'.
            log_path (str, optional): The log_path directory. Defaults to 'log'.
            reraise_on_exception (bool, optional): Whether to reraise exceptions. Defaults to False.
        """
        self.logger = None
        self.lock = threading.Lock()
        self.set_logger(logger_name, level, log_path)
        self.reraise_on_exception = reraise_on_exception

    def set_logger(self, logger_name, level, root):
        """
        Sets the logger with the specified name, log level, and root directory.

        Args:
            logger_name (str): The name of the logger.
            level (str): The log level.
            root (str): The root directory.

        Raises:
            ValueError: If an invalid log level is provided.
        """
        if level not in self.VALID_LOG_LEVELS:
            raise ValueError(f"Invalid log level: {level}. Valid levels are {', '.join(self.VALID_LOG_LEVELS)}")

        self.logger = self.setup_logger(logger_name, level, root)

    def setup_logger(self, logger_name, level, root):
        """
        Configures the logger with the specified name, log level, and root directory.

        Args:
            logger_name (str): The name of the logger.
            level (str): The log level.
            root (str): The root directory.

        Returns:
            logging.Logger: The configured logger.
        """
        if logger_name is None:
            os.makedirs(root, exist_ok=True)
            logger_name = os.path.join(root, f'{datetime.date.today():%d-%b-%Y}.log')

        logger = logging.getLogger(logger_name)
        logger.setLevel(level)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Use RotatingFileHandler to rotate and compress log files
        file_handler = RotatingFileHandler(logger_name, maxBytes=1024*1024, backupCount=5)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

        return logger

    def log_exception(self, func):
        """
        Decorator method that logs exceptions raised in the decorated function with the logger.

        Args:
            func (function): The function to be decorated.

        Returns:
            function: The decorated function.
        """
        def wrapper(*args, **kwargs):
            with self.lock:
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    traceback_str = traceback.format_exc()
                    self.logger.error(f'Exception raised in {func.__name__}. Traceback:\n{traceback_str}')
                    if self.reraise_on_exception:
                        raise e
                    return None
        return wrapper


if __name__ == '__main__':
    logger = ExceptionLogger(level='DEBUG')  # Create an instance of the ExceptionLogger

    # @logger.log_exception
    def divide(a, b):
        return a / b

    result = divide(10, 0)  # This will log the exception and return None