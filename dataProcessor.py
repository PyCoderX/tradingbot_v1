import contextlib
import datetime
import os
import pandas as pd
import queue
import threading


class DataProcessor:
    """
    A class for processing and forwarding real-time data messages received from a queue to another queue and storage.

    Attributes:
        data_queue (queue.Queue): The input queue where data messages are received.
        data_forward (queue.Queue): The output queue where processed data is forwarded.
        log_path (str): The path to the log directory for storing data.

    Methods:
        process_data(self, message): Process the received data message, append it to storage, and forward it.
    """

    def __init__(
        self,
        data_queue,
        data_forward_queue,
        log_path,
        market_time=datetime.time(15, 30),
    ):
        """
        Initializes an instance of the DataProcessor.

        Args:
            data_queue (queue.Queue): The input queue where data messages are received.
            data_forward_queue (queue.Queue): The output queue for forwarding processed data.
            log_path (str): The path to the log directory for storing data.
        """
        self.data_queue = data_queue
        self.root = log_path
        self.data_forward = data_forward_queue
        self.market_time = market_time
        self.lock = threading.Lock()  # Create a lock for thread safety

    def process_data(self, message):
        """
        Process the received data message, append it to storage, and forward it to the data_forward queue.

        Args:
            message (dict): The data message received from the input queue.
        """

        if message.get("ltp"):
            postData = pd.DataFrame.from_dict(message, orient="index").T
            os.makedirs(self.root, exist_ok=True)  # Create the log directory
            fpath = f"{self.root}/realtimeData.csv"
            if os.path.exists(fpath):
                postData.to_csv(fpath, index=False, mode="a", header=False)

                # Acquire the lock before making changes to ensure thread safety
                with self.lock:
                    data = pd.read_csv(fpath)
                    self.data_forward.put(data)

            else:
                postData.to_csv(fpath, index=False)

                with self.lock:
                    self.data_forward.put(postData)

            self.data_forward.task_done()

    def process_data_continuous(self):
        """
        Continuously processes data messages from the input queue and forwards them to the output queue.
        """
        while datetime.datetime.now().time() < self.market_time:
            try:
                # Non-blocking get from the queue with a timeout of 1 second
                message = self.data_queue.get(block=False, timeout=1)
                # print("Received:", datetime.datetime.now())
                # print("Received:", message)
                if message is None:
                    break
                self.process_data(message)
            except queue.Empty:
                pass
            except Exception as e:
                print(e)

    def __call__(self):
        data_processor_thread = threading.Thread(target=self.process_data_continuous)
        data_processor_thread.setDaemon(True)
        return data_processor_thread
