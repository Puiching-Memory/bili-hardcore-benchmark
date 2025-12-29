"""B站 API 客户端基类

使用 httpx 实现，提供统一的请求处理、错误处理和重试逻辑。
"""

import hashlib
import time
import urllib.parse
from typing import Any, Dict, Optional, Type, TypeVar

import httpx
from pydantic import TypeAdapter

from ...core.exceptions import APIError
from ...core.models import BiliResponse

T = TypeVar("T")


class BilibiliClient:
    APPKEY = "783bbb7264451d82"
    APPSEC = "2653583c8873dea268ab9386918b1d65"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 BiliDroid/1.12.0",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    def __init__(self, timeout: int = 30):
        self.client = httpx.Client(timeout=timeout, headers=self.HEADERS)

    def _app_sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        params = {**params, "ts": str(int(time.time())), "appkey": self.APPKEY}
        query = urllib.parse.urlencode(dict(sorted(params.items())))
        params["sign"] = hashlib.md5((query + self.APPSEC).encode()).hexdigest()
        return params

    def _request(
        self,
        method: str,
        url: str,
        model: Type[T],
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> T:
        resp = self.client.request(method, url, params=self._app_sign(params or {}), **kwargs)
        adapter: TypeAdapter[BiliResponse[T]] = TypeAdapter(BiliResponse[model])  # type: ignore
        result = adapter.validate_python(resp.json())
        if not result.is_success:
            raise APIError(result.message, result.code)
        if result.data is None:
            return {}  # type: ignore
        return result.data

    def get(self, url: str, model: Type[T], params: Optional[Dict[str, Any]] = None) -> T:
        return self._request("GET", url, model, params)

    def post(self, url: str, model: Type[T], params: Optional[Dict[str, Any]] = None) -> T:
        return self._request("POST", url, model, params)
