"""自定义异常体系

定义项目中使用的所有自定义异常类型，便于错误处理和调试。
"""

from typing import Any


class BiliHardcoreError(Exception):
    """基础异常类，所有自定义异常的父类"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        """初始化异常

        Args:
            message: 错误消息
            details: 额外的错误详情字典
        """
        self.message = message
        self.details: dict[str, Any] = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ConfigError(BiliHardcoreError):
    """配置错误

    当配置文件缺失、格式错误或必需配置项未提供时抛出。
    """

    pass


class AuthError(BiliHardcoreError):
    """认证错误

    登录失败、token 过期、权限不足等认证相关错误。
    """

    pass


class APIError(BiliHardcoreError):
    """API 调用错误

    B站 API 调用失败、网络错误、响应格式错误等。
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response: dict[str, Any] | None = None,
    ):
        """初始化 API 错误

        Args:
            message: 错误消息
            status_code: HTTP 状态码
            response: API 响应内容
        """
        details: dict[str, Any] = {}
        if status_code is not None:
            details["status_code"] = status_code
        if response is not None:
            details["response"] = response
        super().__init__(message, details)
        self.status_code = status_code
        self.response = response


class QuizError(BiliHardcoreError):
    """答题错误

    答题流程中的业务逻辑错误，如题目获取失败、答案提交失败等。
    """

    pass


class DataError(BiliHardcoreError):
    """数据错误

    数据持久化、序列化、验证等相关错误。
    """

    pass
