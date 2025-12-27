"""B站认证API客户端"""

from typing import Any, Dict

from ...common.exceptions import AuthError
from .client import BilibiliClient


class BilibiliAuthClient(BilibiliClient):
    """B站认证 API 客户端"""

    def get_qrcode(self) -> Dict[str, str]:
        """获取二维码登录信息

        Returns:
            包含 url 和 auth_code 的字典
            {
                'url': str,  # 二维码 URL
                'auth_code': str  # 认证码
            }

        Raises:
            AuthError: 如果获取失败
        """
        url = "https://passport.bilibili.com/x/passport-tv-login/qrcode/auth_code"
        params = {"local_id": 0}

        response = self.post(url, params)

        if response.get("code") == 0:
            data = response.get("data", {})
            return data if isinstance(data, dict) else {}
        else:
            raise AuthError(
                f"获取二维码失败: {response.get('message', 'Unknown error')}", details=response
            )

    def poll_qrcode(self, auth_code: str) -> Dict[str, Any]:
        """轮询二维码登录状态

        Args:
            auth_code: 认证码

        Returns:
            登录结果
            {
                'code': int,  # 0 表示成功
                'data': {
                    'access_token': str,
                    'mid': int,
                    'cookie_info': {
                        'cookies': list
                    }
                }
            }

        Raises:
            AuthError: 如果轮询失败
        """
        url = "https://passport.bilibili.com/x/passport-tv-login/qrcode/poll"
        params = {"auth_code": auth_code, "local_id": 0}

        return self.post(url, params)
