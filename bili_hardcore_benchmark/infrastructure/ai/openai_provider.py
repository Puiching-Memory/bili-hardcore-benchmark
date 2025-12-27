"""OpenAI 提供者实现

使用 OpenAI API（或兼容接口）进行答题预测。
"""

import time

from loguru import logger
from openai import OpenAI

from ...common.exceptions import QuizError
from .provider import AIProviderBase


class OpenAIProvider(AIProviderBase):
    """OpenAI API 提供者"""

    # 提示词模板
    PROMPT_TEMPLATE = """当前时间：{timestamp}
你是一个高效精准的答题专家，面对选择题时，直接根据问题和选项判断正确答案，
并返回对应选项的序号（1, 2, 3, 4）。

示例：
问题：大的反义词是什么？
选项：['长', '宽', '小', '热']
回答：3

如果不确定正确答案，选择最接近的选项序号返回，不提供额外解释或超出 1-4 的内容。

---
请回答我的问题：{question}
"""

    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 30):
        """初始化 OpenAI 提供者

        Args:
            base_url: API base URL
            api_key: API key
            model: 模型名称
            timeout: 超时时间（秒）
        """
        self.client = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout)
        self.model = model
        self.timeout = timeout

    def predict(self, question: str, choices: list[str]) -> int:
        """预测答案

        Args:
            question: 题目内容
            choices: 选项列表

        Returns:
            预测的答案索引（0-based）

        Raises:
            QuizError: 如果 API 调用失败或响应无效
        """
        # 格式化选项
        options_text = ", ".join([f"{i}. {choice}" for i, choice in enumerate(choices, 1)])
        formatted_question = f"题目: {question}\n选项: {options_text}"

        # 构造完整提示词
        prompt = self.PROMPT_TEMPLATE.format(
            timestamp=int(time.time()), question=formatted_question
        )

        try:
            logger.debug(f"调用 AI 预测: {question[:50]}...")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                timeout=self.timeout,
            )

            ai_response = response.choices[0].message.content
            if ai_response is None:
                raise QuizError("AI 返回了空响应")

            ai_response = ai_response.strip()
            logger.debug(f"AI 响应: {ai_response}")

            # 解析答案
            answer_idx = self._parse_answer(ai_response, len(choices))

            if answer_idx is None:
                raise QuizError(
                    f"无法从 AI 响应中提取有效答案: {ai_response}",
                    details={"response": ai_response},
                )

            logger.debug(f"AI 预测答案索引: {answer_idx}")
            return answer_idx

        except Exception as e:
            if isinstance(e, QuizError):
                raise
            logger.error(f"AI 预测失败: {e}")
            raise QuizError(f"AI 预测失败: {e}") from e
