import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FyersCredentials:
    app_id: str = field(repr=False, default=os.environ.get("fyers_app_id"))
    app_type: str = field(repr=False, default=os.environ.get("fyers_app_type"))
    secret_key: str = field(repr=False, default=os.environ.get("fyers_secret_key"))
    fyers_id: str = field(repr=False, default=os.environ.get("fyers_id"))
    totp_key: str = field(repr=False, default=os.environ.get("fyers_totp_key"))
    userpin: str = field(repr=False, default=str(os.environ.get("fyers_userpin")))
    redirect_uri: str = field(
        repr=False, default="https://trade.fyers.in/api-login/redirect-uri/index.html"
    )
