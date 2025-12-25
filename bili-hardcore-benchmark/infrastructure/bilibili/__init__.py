"""B站 API 客户端模块"""

from .client import BilibiliClient
from .auth import BilibiliAuthClient
from .user import BilibiliUserClient
from .senior import BilibiliSeniorClient

__all__ = [
    "BilibiliClient",
    "BilibiliAuthClient",
    "BilibiliUserClient",
    "BilibiliSeniorClient",
]

