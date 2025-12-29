"""AI 提供者基类

定义 AI 提供者的接口和通用逻辑。
"""

from abc import ABC, abstractmethod
from typing import Optional


class AIProviderBase(ABC):
    """AI 提供者抽象基类"""

    @abstractmethod
    def predict(self, question: str, choices: list[str]) -> int:
        """预测答案

        Args:
            question: 题目内容
            choices: 选项列表

        Returns:
            预测的答案索引（0-based）

        Raises:
            ValueError: 如果预测失败或返回无效索引
        """
        pass

    def _parse_answer(self, response: str, num_choices: int) -> Optional[int]:
        """解析 AI 响应，提取答案索引

        Args:
            response: AI 响应文本
            num_choices: 选项数量

        Returns:
            答案索引（0-based），如果解析失败返回 None
        """
        import re

        response = response.strip()

        # 1. 尝试匹配常见的答案格式（优先级最高）
        patterns = [
            r"(?:回答|答案|选项|选择|index|result)[:：]\s*(\d+)",
            r"正确答案是[:：]?\s*(\d+)",
            r"应该选[:：]?\s*(\d+)",
            r"(\d+)\s*是正确答案",
        ]
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                try:
                    answer = int(match.group(1))
                    if 1 <= answer <= num_choices:
                        return answer - 1
                    if 0 <= answer < num_choices:
                        return answer
                except ValueError:
                    continue

        # 2. 尝试直接解析为整数
        try:
            # 支持 1-based（1,2,3,4）和 0-based（0,1,2,3）
            answer = int(response)

            # 如果是 1-based，转换为 0-based
            if 1 <= answer <= num_choices:
                return answer - 1

            # 如果已经是 0-based
            if 0 <= answer < num_choices:
                return answer
        except ValueError:
            pass

        # 3. 尝试从文本中提取数字，从后往前找（通常结论在最后）
        numbers = re.findall(r"\d+", response)
        if numbers:
            for num_str in reversed(numbers):
                try:
                    answer = int(num_str)
                    if 1 <= answer <= num_choices:
                        return answer - 1
                    if 0 <= answer < num_choices:
                        return answer
                except ValueError:
                    continue

        return None
