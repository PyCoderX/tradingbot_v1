import os
import utils as utils


class TelegramCredentials:
    token = os.environ.get("telegram_token")
    group_chat_id = os.environ.get("telegram_group_chat_id")
    personal_chat_id = os.environ.get("telegram_personal_chat_id")


class TelegramBot:
    """
    A class for interacting with the Telegram Bot API using TelegramCredentials.

    Attributes:
        base_url (str): The base URL for making API requests.
    """

    def __init__(self, log_path: str = "log"):
        # API
        self.base_url = f"https://api.telegram.org/bot{TelegramCredentials.token}/"
        self.log_path = log_path
        os.makedirs(self.log_path, exist_ok=True)

    def make_request(self, func):
        # create a looger instance
        logger = utils.ExceptionLogger(
            level="DEBUG", log_path=self.log_path, reraise_on_exception=False)
        # create a HTTP request handler
        client = utils.RestClient()
        wrapper = logger.log_exception(client.request(func))
        return wrapper()

    def sendMessage(self, text):
        """
        Send a text message via the Telegram Bot API.

        Args:
            text (str): The text of the message.

        Returns:
            dict: The API request parameters.
        """
        inputs = {"method": "POST", "url": f"{self.base_url}sendMessage", "params": {
            "chat_id": TelegramCredentials.personal_chat_id, "text": text}}
        return self.make_request(lambda: inputs)

    def sendDocument(self, document_path, caption=""):
        """
        Send a document via the Telegram Bot API.

        Args:
            document_path (str): The path to the document file.
            caption (str, optional): The caption for the document (default is '').

        Returns:
            dict: The API request parameters.
        """
        try:
            inputs = {
                "method": "POST",
                "url": f"{self.base_url}sendDocument",
                "params": {"chat_id": TelegramCredentials.personal_chat_id, "caption": caption},
                "files": {"document": open(document_path, "rb")},
            }
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File not found: {str(e)}")
        except Exception as e:
            raise e
        return self.make_request(lambda: inputs)

    def sendPhoto(self, photo_path, caption=""):
        """
        Send a photo via the Telegram Bot API.

        Args:
            photo_path (str): The path to the photo file.
            caption (str, optional): The caption for the photo (default is '').

        Returns:
            dict: The API request parameters.
        """
        try:
            inputs = {
                "method": "POST",
                "url": f"{self.base_url}sendPhoto",
                "params": {"chat_id": TelegramCredentials.personal_chat_id, "caption": caption},
                "files": {"photo": open(photo_path, "rb")},
            }
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File not found: {str(e)}")
        except Exception as e:
            raise e
        return self.make_request(lambda: inputs)


if __name__ == "__main__":
    telebot = TelegramBot(log_path=f"{os.getcwd()}/log")
    telebot.sendMessage("Hello world")
