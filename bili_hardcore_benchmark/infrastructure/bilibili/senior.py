from typing import Any, Dict

from ...core.models import BiliQuestion, BiliResult
from .client import BilibiliClient


class BilibiliSeniorClient(BilibiliClient):
    def __init__(self, access_token: str, csrf: str, timeout: int = 30):
        super().__init__(timeout)
        self.access_token, self.csrf = access_token, csrf

    def _params(self) -> Dict[str, Any]:
        return {
            "access_key": self.access_token,
            "csrf": self.csrf,
            "mobi_app": "android",
            "platform": "android",
        }

    def get_question(self) -> BiliQuestion:
        return self.get(
            "https://api.bilibili.com/x/senior/v1/question", BiliQuestion, self._params()
        )

    def submit_answer(self, qid: int, ans_hash: str, ans_text: str) -> Dict[str, Any]:
        params = {**self._params(), "id": qid, "ans_hash": ans_hash, "ans_text": ans_text}
        return self.post(
            "https://api.bilibili.com/x/senior/v1/answer/submit",
            Dict[str, Any],
            params,
        )

    def get_result(self) -> BiliResult:
        return self.get(
            "https://api.bilibili.com/x/senior/v1/answer/result",
            BiliResult,
            self._params(),
        )
