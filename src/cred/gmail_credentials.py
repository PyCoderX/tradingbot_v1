import os
from dataclasses import dataclass


@dataclass
class GmailCredentials:
    gmail_username = os.environ.get("gmail_username")
    gmail_password = os.environ.get("gmail_password")
