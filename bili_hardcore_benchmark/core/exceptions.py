from typing import Any, Dict, Optional


class BiliHardcoreError(Exception):
    """Base exception"""

    pass


class APIError(BiliHardcoreError):
    """API error"""

    def __init__(self, message: str, code: int = -1):
        super().__init__(message)
        self.code = code


class AuthError(BiliHardcoreError):
    """Auth error"""

    pass


class QuizError(BiliHardcoreError):
    """Quiz error"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}
