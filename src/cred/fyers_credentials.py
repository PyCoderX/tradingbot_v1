import os
from dataclasses import dataclass


@dataclass
class FyesrCredentials:
    app_id: str = os.environ.get("fyers_app_id")
    app_type: str = os.environ.get("fyers_app_type")
    secret_key: str = os.environ.get("fyers_secret_key")
    fyers_id: str = os.environ.get("fyers_id")
    totp_key: str = os.environ.get("fyers_totp_key")
    userpin: str = str(os.environ.get("fyers_userpin"))
    redirect_uri: str = "https://trade.fyers.in/api-login/redirect-uri/index.html"
