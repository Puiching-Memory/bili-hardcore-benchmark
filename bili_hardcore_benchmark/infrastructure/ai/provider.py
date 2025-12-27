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
        # 尝试提取数字
        response = response.strip()

        # 尝试直接解析为整数
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

        # 尝试从文本中提取第一个数字
        import re

        numbers = re.findall(r"\d+", response)
        if numbers:
            try:
                answer = int(numbers[0])
                if 1 <= answer <= num_choices:
                    return answer - 1
                if 0 <= answer < num_choices:
                    return answer
            except ValueError:
                pass

        return None
