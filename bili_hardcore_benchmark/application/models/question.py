"""题目模型

单选题逻辑的数据模型，支持增量更新答案状态。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class QuestionStatus(Enum):
    """题目状态枚举"""

    UNKNOWN = "unknown"  # 完全未知
    PARTIAL = "partial"  # 部分已知（有错误答案记录）
    COMPLETE = "complete"  # 已完整（正确答案已知）


@dataclass
class Question:
    """题目实体

    单选题约束：correct_answer 存在时，其他选项自动为错误。
    """

    id: str
    question: str
    choices: list[str]
    category: Optional[str] = None
    correct_answer: Optional[int] = None  # 0-based 索引
    wrong_answers: list[int] = field(default_factory=list)
    attempts: int = 0
    last_attempt: Optional[datetime] = None

    def __post_init__(self) -> None:
        """验证数据的一致性"""
        # 确保 choices 不为空
        if not self.choices:
            raise ValueError(f"题目 {self.id} 没有选项")

        # 验证 correct_answer 索引范围
        if self.correct_answer is not None:
            if not 0 <= self.correct_answer < len(self.choices):
                raise ValueError(
                    f"题目 {self.id} 的正确答案索引 {self.correct_answer} "
                    f"超出范围 [0, {len(self.choices)})"
                )

        # 验证 wrong_answers 索引范围
        for idx in self.wrong_answers:
            if not 0 <= idx < len(self.choices):
                raise ValueError(
                    f"题目 {self.id} 的错误答案索引 {idx} " f"超出范围 [0, {len(self.choices)})"
                )

    @property
    def status(self) -> QuestionStatus:
        """获取题目状态"""
        if self.correct_answer is not None:
            return QuestionStatus.COMPLETE
        elif self.wrong_answers:
            return QuestionStatus.PARTIAL
        else:
            return QuestionStatus.UNKNOWN

    def is_complete(self) -> bool:
        """是否已完整（已知正确答案）"""
        return self.correct_answer is not None

    def is_partial(self) -> bool:
        """是否部分已知"""
        return self.correct_answer is None and len(self.wrong_answers) > 0

    def is_unknown(self) -> bool:
        """是否完全未知"""
        return self.correct_answer is None and len(self.wrong_answers) == 0

    def get_untried_choices(self) -> list[int]:
        """获取未尝试的选项索引列表

        Returns:
            未尝试的选项索引列表（0-based）
        """
        if self.correct_answer is not None:
            # 已知正确答案，所有其他选项都是错误的
            return []

        # 返回未在 wrong_answers 中的选项
        all_indices = set(range(len(self.choices)))
        tried_indices = set(self.wrong_answers)
        return sorted(list(all_indices - tried_indices))

    def get_wrong_choices(self) -> list[int]:
        """获取错误选项索引列表

        Returns:
            错误选项索引列表（0-based）
        """
        if self.correct_answer is not None:
            # 已知正确答案，返回所有其他选项
            return [i for i in range(len(self.choices)) if i != self.correct_answer]
        else:
            # 未知正确答案，返回已知的错误选项
            return self.wrong_answers.copy()

    def mark_as_correct(self, answer_index: int) -> None:
        """标记正确答案

        Args:
            answer_index: 正确答案索引（0-based）

        Raises:
            ValueError: 如果索引超出范围
        """
        if not 0 <= answer_index < len(self.choices):
            raise ValueError(f"答案索引 {answer_index} 超出范围")

        self.correct_answer = answer_index
        self.attempts += 1
        self.last_attempt = datetime.now()

    def mark_as_wrong(self, answer_index: int) -> None:
        """标记错误答案

        Args:
            answer_index: 错误答案索引（0-based）

        Raises:
            ValueError: 如果索引超出范围或已知正确答案
        """
        if not 0 <= answer_index < len(self.choices):
            raise ValueError(f"答案索引 {answer_index} 超出范围")

        if self.correct_answer is not None:
            raise ValueError("题目已有正确答案，不能再标记错误答案")

        if answer_index not in self.wrong_answers:
            self.wrong_answers.append(answer_index)

        self.attempts += 1
        self.last_attempt = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式（用于持久化）

        注意：不包含 id 字段，因为它已经是字典的 key
        """
        data: dict[str, Any] = {
            "question": self.question,
            "choices": self.choices,
            "attempts": self.attempts,
        }

        if self.category is not None:
            data["category"] = self.category

        if self.correct_answer is not None:
            data["correct_answer"] = self.correct_answer

        if self.wrong_answers:
            data["wrong_answers"] = self.wrong_answers

        if self.last_attempt is not None:
            data["last_attempt"] = self.last_attempt.isoformat()

        return data

    @classmethod
    def from_dict(cls, question_id: str, data: dict[str, Any]) -> "Question":
        """从字典创建题目实例

        Args:
            question_id: 题目ID（来自字典的 key）
            data: 题目数据字典（不包含 id，或包含但被忽略）

        Returns:
            Question 实例
        """
        last_attempt = None
        if "last_attempt" in data and data["last_attempt"]:
            last_attempt = datetime.fromisoformat(data["last_attempt"])

        return cls(
            id=question_id,
            question=data["question"],
            choices=data["choices"],
            category=data.get("category"),
            correct_answer=data.get("correct_answer"),
            wrong_answers=data.get("wrong_answers", []),
            attempts=data.get("attempts", 0),
            last_attempt=last_attempt,
        )
