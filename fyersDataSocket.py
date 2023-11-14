from fyers_apiv3.FyersWebsocket import data_ws
from pathlib import Path


class DataSocket:
    def __init__(self, access_token, symbols, data_queue, log_path: str | Path = ""):
        self.access_token = access_token
        self.symbols = symbols
        self.data_queue = data_queue
        self.log_path = log_path

    def onmessage(self, message):
        """
        Callback function to handle incoming messages from the FyersDataSocket WebSocket.

        Parameters:
            message (dict): The received message from the WebSocket.

        """

        # print("Response:", message)
        self.data_queue.put(message)  # Put the received message in the queue

    def onerror(self, message):
        """
        Callback function to handle WebSocket errors.

        Parameters:
            message (dict): The error message received from the WebSocket.


        """
        print("Error:", message)

    def onclose(self, message):
        """
        Callback function to handle WebSocket connection close events.
        """
        print("Connection closed:", message)

    def onopen(self):
        """
        Callback function to subscribe to data type and symbols upon WebSocket connection.

        """
        # Specify the data type and symbols you want to subscribe to
        self.data_type = "SymbolUpdate"

        # Subscribe to the specified symbols and data type

        self.fyers.subscribe(symbols=self.symbols, data_type=self.data_type)

        # Keep the socket running to receive real-time data
        self.fyers.keep_running()

    def unsubscribe(self):
        self.fyers.unsubscribe(symbols=self.symbols, data_type=self.data_type)

    def __call__(self):
        if self.log_path != "":
            Path.mkdir(self.log_path, exist_ok=True)
        # Create a FyersDataSocket instance with the provided parameters
        self.fyers = data_ws.FyersDataSocket(
            access_token=self.access_token,  # Access token in the format "appid:accesstoken"
            log_path=self.log_path,  # Path to save logs. Leave empty to auto-create logs in the current directory.
            litemode=False,  # Lite mode disabled. Set to True if you want a lite response.
            write_to_file=False,  # Save response in a log file instead of printing it.
            reconnect=True,  # Enable auto-reconnection to WebSocket on disconnection.
            on_connect=self.onopen,  # Callback function to subscribe to data upon connection.
            on_close=self.onclose,  # Callback function to handle WebSocket connection close events.
            on_error=self.onerror,  # Callback function to handle WebSocket errors.
            on_message=self.onmessage,  # Callback function to handle incoming messages from the WebSocket.
        )

        # Establish a connection to the Fyers WebSocket
        self.fyers.connect()
