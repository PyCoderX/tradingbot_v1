import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GmailCredentials:
    gmail_username: str = field(default=os.environ.get("gmail_username"), repr=False)
    gmail_password: str = field(default=os.environ.get("gmail_password"), repr=False)
