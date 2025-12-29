from ...core.models import LoginData, QRCodeData
from .client import BilibiliClient


class BilibiliAuthClient(BilibiliClient):
    def get_qrcode(self) -> QRCodeData:
        return self.post(
            "https://passport.bilibili.com/x/passport-tv-login/qrcode/auth_code",
            QRCodeData,
            {"local_id": 0},
        )

    def poll_qrcode(self, auth_code: str) -> LoginData:
        return self.post(
            "https://passport.bilibili.com/x/passport-tv-login/qrcode/poll",
            LoginData,
            {"auth_code": auth_code, "local_id": 0},
        )
