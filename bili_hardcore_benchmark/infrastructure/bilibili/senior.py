"""B站硬核会员答题API客户端"""

from typing import Any, Dict

from ...common.exceptions import APIError
from .client import BilibiliClient


class BilibiliSeniorClient(BilibiliClient):
    """B站硬核会员答题 API 客户端"""

    def __init__(self, access_token: str, csrf: str, timeout: int = 30, max_retries: int = 3):
        """初始化答题 API 客户端

        Args:
            access_token: 访问令牌
            csrf: CSRF 令牌
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        super().__init__(timeout, max_retries)
        self.access_token = access_token
        self.csrf = csrf

    def _get_common_params(self) -> Dict[str, Any]:
        """获取通用请求参数"""
        return {
            "access_key": self.access_token,
            "csrf": self.csrf,
            "disable_rcmd": "0",
            "mobi_app": "android",
            "platform": "android",
            "statistics": '{"appId":1,"platform":3,"version":"8.40.0","abtest":""}',
            "web_location": "333.790",
        }

    def get_question(self) -> Dict[str, Any]:
        """获取题目

        Returns:
            题目信息
            {
                'code': int,  # 0 表示成功，非0可能需要验证码
                'data': {
                    'id': int,  # 题目 ID
                    'question': str,  # 题目内容
                    'answers': [
                        {
                            'ans_text': str,
                            'ans_hash': str
                        }
                    ],
                    'question_num': int  # 当前题号
                }
            }

        Raises:
            QuizError: 如果获取失败
        """
        url = "https://api.bilibili.com/x/senior/v1/question"
        params = self._get_common_params()

        return self.get(url, params)

    def submit_answer(self, question_id: int, ans_hash: str, ans_text: str) -> Dict[str, Any]:
        """提交答案

        Args:
            question_id: 题目 ID
            ans_hash: 答案哈希
            ans_text: 答案文本

        Returns:
            提交结果
            {
                'code': int,  # 0 表示成功
                ...
            }

        Raises:
            QuizError: 如果提交失败
        """
        url = "https://api.bilibili.com/x/senior/v1/answer/submit"
        params = self._get_common_params()
        params.update({"id": question_id, "ans_hash": ans_hash, "ans_text": ans_text})

        return self.post(url, params)

    def get_result(self) -> Dict[str, Any]:
        """获取答题结果

        Returns:
            答题结果
            {
                'score': int,  # 总分数
                'scores': [
                    {
                        'category': str,  # 分类名称
                        'score': int,  # 该分类得分
                        'total': int  # 该分类总分
                    }
                ]
            }

        Raises:
            APIError: 如果请求失败
        """
        url = "https://api.bilibili.com/x/senior/v1/answer/result"
        params = self._get_common_params()

        response = self.get(url, params)

        if response.get("code") == 0:
            data = response.get("data", {})
            return data if isinstance(data, dict) else {}
        else:
            raise APIError(
                f"获取答题结果失败: {response.get('message', 'Unknown error')}", response=response
            )
