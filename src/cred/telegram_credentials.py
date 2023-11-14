import os
from dataclasses import dataclass, field


@dataclass
class TelegramCredentials:
    token: str = field(default=os.environ.get("telegram_token"), repr=False)
    group_chat_id: str = field(
        default=os.environ.get("telegram_group_chat_id"), repr=False
    )
    personal_chat_id: str = field(
        default=os.environ.get("telegram_personal_chat_id"), repr=False
    )
