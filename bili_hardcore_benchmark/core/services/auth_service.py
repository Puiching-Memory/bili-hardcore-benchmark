import time

from loguru import logger
from qrcode.constants import ERROR_CORRECT_L
from qrcode.main import QRCode

from ...core.exceptions import AuthError
from ...core.models import LoginData
from ...infrastructure.bilibili.auth import BilibiliAuthClient


class AuthService:
    def __init__(self, auth_client: BilibiliAuthClient):
        self.auth_client = auth_client

    def login(self) -> LoginData:
        qr_data = self.auth_client.get_qrcode()
        qr = QRCode(version=1, error_correction=ERROR_CORRECT_L, box_size=2, border=1)
        qr.add_data(qr_data.url)
        qr.print_ascii()
        logger.info(f"请扫码登录: {qr_data.url}")

        for _ in range(60):
            try:
                if login := self.auth_client.poll_qrcode(qr_data.auth_code):
                    logger.info("✅ 登录成功")
                    return login
            except Exception:
                pass
            time.sleep(1)
        raise AuthError("登录超时")
