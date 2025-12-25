"""B站 API 客户端基类

使用 httpx 实现，提供统一的请求处理、错误处理和重试逻辑。
"""

import hashlib
import time
import urllib.parse
from typing import Any, Optional, Dict

import httpx
from loguru import logger

from ...common.exceptions import APIError


class BilibiliClient:
    """B站 API 客户端基类
    
    提供统一的请求方法和 APP 签名。
    """
    
    # APP 签名配置 (参考 https://github.com/Karben233/bili-hardcore)
    APPKEY = '783bbb7264451d82'
    APPSEC = '2653583c8873dea268ab9386918b1d65'
    
    # 通用请求头
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 BiliDroid/1.12.0 (bbcallen@gmail.com)',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'x-bili-metadata-legal-region': 'CN',
        'x-bili-aurora-eid': '',
        'x-bili-aurora-zone': '',
    }
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """初始化客户端
        
        Args:
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.timeout = timeout
        self.max_retries = max_retries
        
        # 创建 httpx 客户端
        self.client = httpx.Client(
            timeout=timeout,
            headers=self.HEADERS.copy(),
            transport=httpx.HTTPTransport(retries=max_retries)
        )
    
    def __enter__(self) -> "BilibiliClient":
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """上下文管理器退出"""
        self.close()
    
    def close(self) -> None:
        """关闭客户端"""
        self.client.close()
    
    def _app_sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """为请求参数进行 APP 签名
        
        Args:
            params: 请求参数
            
        Returns:
            添加签名后的参数
        """
        # 添加时间戳和 appkey
        params = params.copy()
        params['ts'] = str(int(time.time()))
        params['appkey'] = self.APPKEY
        
        # 排序参数
        sorted_params = dict(sorted(params.items()))
        
        # 生成签名
        query = urllib.parse.urlencode(sorted_params)
        sign = hashlib.md5((query + self.APPSEC).encode()).hexdigest()
        params['sign'] = sign
        
        return params
    
    def _request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """发送HTTP请求
        
        Args:
            method: HTTP 方法（GET, POST 等）
            url: 请求 URL
            params: 请求参数
            **kwargs: 其他 httpx 参数
            
        Returns:
            响应数据（JSON）
            
        Raises:
            APIError: 如果请求失败或响应无效
        """
        params = params or {}
        
        # APP 签名
        signed_params = self._app_sign(params)
        
        try:
            logger.debug(f"{method} {url}")
            
            if method.upper() == 'GET':
                response = self.client.get(url, params=signed_params, **kwargs)
            elif method.upper() == 'POST':
                response = self.client.post(url, data=signed_params, **kwargs)
            else:
                raise ValueError(f"不支持的 HTTP 方法: {method}")
            
            # 检查 HTTP 状态码
            response.raise_for_status()
            
            # 解析 JSON
            data = response.json()
            
            # 检查业务状态码
            if not isinstance(data, dict):
                raise APIError(
                    "响应数据格式错误：不是字典",
                    response=data
                )
            
            logger.debug(f"响应: code={data.get('code')}")
            
            return data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP 错误: {e.response.status_code}")
            raise APIError(
                f"HTTP 请求失败: {e.response.status_code}",
                status_code=e.response.status_code,
                response=e.response.text
            ) from e
        except httpx.RequestError as e:
            logger.error(f"请求错误: {e}")
            raise APIError(f"网络请求失败: {e}") from e
        except ValueError as e:
            logger.error(f"JSON 解析失败: {e}")
            raise APIError(f"响应JSON解析失败: {e}") from e
    
    def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送 GET 请求
        
        Args:
            url: 请求 URL
            params: 请求参数
            
        Returns:
            响应数据
        """
        return self._request('GET', url, params)
    
    def post(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送 POST 请求
        
        Args:
            url: 请求 URL
            params: 请求参数
            
        Returns:
            响应数据
        """
        return self._request('POST', url, params)

