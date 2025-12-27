"""基准测试模型

管理题目集合和统计信息。
"""

from dataclasses import dataclass
from typing import Any, Dict

from .question import Question


@dataclass
class BenchmarkStatistics:
    """基准测试统计信息"""

    total_questions: int
    complete_questions: int
    partial_questions: int
    unknown_questions: int
    completion_rate: float

    def __str__(self) -> str:
        """格式化输出统计信息"""
        return (
            f"总题数: {self.total_questions}\n"
            f"  - 完整题目: {self.complete_questions}\n"
            f"  - 部分已知: {self.partial_questions}\n"
            f"  - 完全未知: {self.unknown_questions}\n"
            f"完成率: {self.completion_rate:.2f}%"
        )


class Benchmark:
    """基准测试聚合根

    管理题目集合，提供统计和查询功能。
    """

    def __init__(self) -> None:
        """初始化空的基准测试"""
        self._questions: Dict[str, Question] = {}

    def add_question(self, question: Question) -> None:
        """添加或更新题目

        Args:
            question: 题目实例
        """
        self._questions[question.id] = question

    def get_question(self, question_id: str) -> Question | None:
        """获取题目

        Args:
            question_id: 题目ID

        Returns:
            题目实例，如果不存在返回 None
        """
        return self._questions.get(question_id)

    def has_question(self, question_id: str) -> bool:
        """检查题目是否存在

        Args:
            question_id: 题目ID

        Returns:
            是否存在
        """
        return question_id in self._questions

    def get_all_questions(self) -> list[Question]:
        """获取所有题目

        Returns:
            题目列表
        """
        return list(self._questions.values())

    def get_complete_questions(self) -> list[Question]:
        """获取所有完整题目（已知正确答案）

        Returns:
            完整题目列表
        """
        return [q for q in self._questions.values() if q.is_complete()]

    def get_partial_questions(self) -> list[Question]:
        """获取所有部分已知题目

        Returns:
            部分已知题目列表
        """
        return [q for q in self._questions.values() if q.is_partial()]

    def get_unknown_questions(self) -> list[Question]:
        """获取所有未知题目

        Returns:
            未知题目列表
        """
        return [q for q in self._questions.values() if q.is_unknown()]

    def get_statistics(self) -> BenchmarkStatistics:
        """获取统计信息

        Returns:
            统计信息对象
        """
        total = len(self._questions)
        complete = len(self.get_complete_questions())
        partial = len(self.get_partial_questions())
        unknown = len(self.get_unknown_questions())
        completion_rate = (complete / total * 100) if total > 0 else 0.0

        return BenchmarkStatistics(
            total_questions=total,
            complete_questions=complete,
            partial_questions=partial,
            unknown_questions=unknown,
            completion_rate=completion_rate,
        )

    def to_dict(self) -> dict[str, dict[str, Any]]:
        """转换为字典格式（用于持久化）

        Returns:
            题目ID到题目数据的映射
        """
        return {qid: q.to_dict() for qid, q in self._questions.items()}

    @classmethod
    def from_dict(cls, data: dict[str, dict[str, Any]]) -> "Benchmark":
        """从字典创建基准测试实例

        Args:
            data: 题目ID到题目数据的映射

        Returns:
            Benchmark 实例
        """
        benchmark = cls()
        for question_id, question_data in data.items():
            question = Question.from_dict(question_id, question_data)
            benchmark.add_question(question)
        return benchmark
