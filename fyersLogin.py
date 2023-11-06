import os
import pyotp
from urllib.parse import parse_qs, urlparse
import utils as utils

import fyersModel

client = utils.RestClient()  # Create an instance of the RestClient


class FyersCredentials:
    app_id = os.environ.get("fyers_app_id")
    app_type = os.environ.get("fyers_app_type")
    secret_key = os.environ.get("fyers_secret_key")
    fyers_id = os.environ.get("fyers_id")
    totp_key = os.environ.get("fyers_totp_key")
    userpin = str(os.environ.get("fyers_userpin"))
    redirect_uri = "https://trade.fyers.in/api-login/redirect-uri/index.html"


class FyersLogin(FyersCredentials, utils.ExceptionLogger):
    """
    FyersLogin class for handling the login process with Fyers API.
    """

    def __init__(self, log_path, teleBot=None):
        """
        Initializes a new instance of FyersLogin.

        This constructor sets up the necessary URLs, endpoints, and initializes variables for API responses.
        """
        FyersCredentials.__init__(self)
        utils.ExceptionLogger.__init__(self, level="DEBUG", log_path=log_path)
        # URLs
        self.loginAPI = "https://api-t2.fyers.in/vagator/v2"
        self.API = "https://api-t1.fyers.in/api/v3"

        # Endpoints
        self.otp = "/send_login_otp"
        self.totp = "/verify_otp"
        self.pin = "/verify_pin"
        self.token = "/token"

        # API response data
        self.data = {}
        self.access_token = None

        # Log Path
        self.log_path = log_path
        os.makedirs(self.log_path, exist_ok=True)

        # set bot
        self.teleBot = teleBot
        # print

        # Client ID
        self.client_id = f"{self.app_id}-{self.app_type}"

        # login

        self.log_exception(self.login)()

    def sendMessage(self, message):
        if self.teleBot:
            self.teleBot.sendMessage(message)
        else:
            print(message)

    @client.request
    def _send_loginOTP(self):
        """
        Sends a login OTP (One-Time Password) request to the Fyers API.

        Returns:
            dict: Input data for the request.
        """
        return {
            "method": "POST",
            "url": f"{self.loginAPI}{self.otp}",
            "json": {"fy_id": self.fyers_id, "app_id": self.app_id},
        }

    @client.request
    def _verifyTOTP(self):
        """
        Verifies a TOTP (Time-Based One-Time Password) with the Fyers API.

        Returns:
            dict: Input data for the request.
        """
        return {
            "method": "POST",
            "url": f"{self.loginAPI}{self.totp}",
            "json": {
                "request_key": self.data.get("request_key"),
                "otp": pyotp.TOTP(self.totp_key).now(),
            },
        }

    @client.request
    def _verifyPIN(self):
        """
        Verifies a PIN with the Fyers API.

        Returns:
            dict: Input data for the request.
        """
        return {
            "method": "POST",
            "url": f"{self.loginAPI}{self.pin}",
            "json": {
                "request_key": self.data.get("request_key"),
                "identity_type": "pin",
                "identifier": self.userpin,
                "recaptcha_token": "",
            },
        }

    @client.request
    def _generateAuthCode(self):
        """
        Generates an authorization code with the Fyers API.

        Returns:
            dict: Input data for the request.
        """
        return {
            "method": "POST",
            "url": f"{self.API}{self.token}",
            "json": {
                "fyers_id": self.fyers_id,
                "app_id": self.app_id,
                "redirect_uri": self.redirect_uri,
                "appType": self.app_type,
                "code_challenge": "",
                "state": "None",
                "scope": "",
                "nonce": "",
                "response_type": "code",
                "create_cookie": True,
            },
            "headers": {
                "authorization": f"Bearer {self.data['data']['access_token']}"
            },
        }

    def _generate_access_token(self):
        """
        Generates an access token using the received authorization code.

        Returns:
            None
        """

        appSession = fyersModel.SessionModel(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            response_type="code",
            state="sample",
            secret_key=self.secret_key,
            grant_type="authorization_code",
        )
        url = self.data.get("Url")
        response = None
        if url:
            parsed = urlparse(url)
            auth_code = parse_qs(parsed.query)["auth_code"][0]
            appSession.set_token(auth_code)
            response = appSession.generate_token()
            self.access_token = response.get("access_token")

        return response

    def _handle_step(self, step_func, step_name):
        self.data = step_func()
        if self.data.get("message"):
            self.sendMessage(f"{step_name} successful: {self.data['message']}")

    @utils.retry(max_attempts=3, initial_delay=3, backoff_factor=2)
    def login(self):
        """
        Performs the Fyers login process, including sending OTP, verifying TOTP, verifying PIN, generating an Auth Code, and generating an Access Token.
        """
        steps = [
            (self._send_loginOTP, "Send login OTP"),
            (self._verifyTOTP, "Verify TOTP"),
            (self._verifyPIN, "Verify PIN"),
            (self._generateAuthCode, "Generate Auth Code"),
            (self._generate_access_token, "Generate Access Token"),
        ]

        for step_func, step_name in steps:
            self._handle_step(step_func, step_name)

        self.sendMessage("Login successful!")
        return True

    def __call__(self):
        return fyersModel.FyersModel(
            client_id=self.client_id,
            token=self.access_token,
        )


if __name__ == "__main__":
    fyers = FyersLogin(log_path=f"{os.getcwd()}/log")
    print(dir(fyers()))
