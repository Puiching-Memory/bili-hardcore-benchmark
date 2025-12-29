from typing import Any, Dict

from .client import BilibiliClient


class BilibiliUserClient(BilibiliClient):
    def __init__(self, access_token: str, timeout: int = 30):
        super().__init__(timeout)
        self.access_token = access_token

    def get_account_info(self) -> Dict[str, Any]:
        return self.get(
            "https://app.bilibili.com/x/v2/account/myinfo",
            Dict[str, Any],
            {"access_key": self.access_token},
        )
