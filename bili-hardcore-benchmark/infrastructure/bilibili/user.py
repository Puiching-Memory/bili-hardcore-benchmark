"""B站用户API客户端"""

from typing import Dict, Any

from .client import BilibiliClient
from ...common.exceptions import APIError


class BilibiliUserClient(BilibiliClient):
    """B站用户 API 客户端"""
    
    def __init__(self, access_token: str, timeout: int = 30, max_retries: int = 3):
        """初始化用户 API 客户端
        
        Args:
            access_token: 访问令牌
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        super().__init__(timeout, max_retries)
        self.access_token = access_token
    
    def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息
        
        Returns:
            账户信息
            {
                'mid': int,  # 用户ID
                'name': str,  # 用户名
                'level': int,  # 用户等级
                ...
            }
            
        Raises:
            APIError: 如果请求失败
        """
        url = 'https://app.bilibili.com/x/v2/account/myinfo'
        params = {
            'access_key': self.access_token
        }
        
        response = self.get(url, params)
        
        if response.get('code') == 0:
            return response.get('data', {})
        else:
            raise APIError(
                f"获取账户信息失败: {response.get('message', 'Unknown error')}",
                response=response
            )

