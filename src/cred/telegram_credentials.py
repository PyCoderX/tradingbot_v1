import os
from dataclasses import dataclass


@dataclass
class TelegramCredentials:
    token: str = os.environ.get("telegram_token")
    group_chat_id: str = os.environ.get("telegram_group_chat_id")
    personal_chat_id: str = os.environ.get("telegram_personal_chat_id")
