"""B站 API 客户端模块"""

from .auth import BilibiliAuthClient
from .client import BilibiliClient
from .senior import BilibiliSeniorClient
from .user import BilibiliUserClient

__all__ = [
    "BilibiliClient",
    "BilibiliAuthClient",
    "BilibiliUserClient",
    "BilibiliSeniorClient",
]
