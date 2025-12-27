"""数据收集服务

负责记录答题结果、管理题目数据和提供统计信息。
"""

from typing import Any, Optional, Protocol

from loguru import logger

from ..models.benchmark import Benchmark, BenchmarkStatistics
from ..models.question import Question


class QuestionStore(Protocol):
    """题目存储协议"""

    def load(self) -> dict[str, dict[str, Any]]:
        """加载所有题目"""
        ...

    def save(self, questions: dict[str, dict[str, Any]]) -> None:
        """保存所有题目"""
        ...


class BenchmarkService:
    """数据收集服务

    管理题目数据的持久化和统计。
    """

    def __init__(self, question_store: QuestionStore):
        """初始化服务

        Args:
            question_store: 题目存储实例
        """
        self.store = question_store
        self.benchmark = Benchmark()
        self._load_data()

    def _load_data(self) -> None:
        """从存储加载数据"""
        try:
            data = self.store.load()
            self.benchmark = Benchmark.from_dict(data)
            stats = self.benchmark.get_statistics()
            logger.info(f"已加载 {stats.total_questions} 道题目")
            logger.info(
                f"  - 完整: {stats.complete_questions}, "
                f"部分已知: {stats.partial_questions}, "
                f"未知: {stats.unknown_questions}"
            )
        except FileNotFoundError:
            logger.info("未找到已有数据，从空状态开始")
        except Exception as e:
            logger.warning(f"加载数据失败: {e}，从空状态开始")

    def _save_data(self) -> None:
        """保存数据到存储"""
        try:
            data = self.benchmark.to_dict()
            self.store.save(data)
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            raise

    def get_or_create_question(
        self,
        question_id: str,
        question_text: str,
        choices: list[str],
        category: Optional[str] = None,
    ) -> Question:
        """获取或创建题目

        Args:
            question_id: 题目ID
            question_text: 题目内容
            choices: 选项列表
            category: 题目分类

        Returns:
            题目实例
        """
        question = self.benchmark.get_question(question_id)

        if question is None:
            # 创建新题目
            question = Question(
                id=question_id,
                question=question_text,
                choices=choices,
                category=category,
            )
            self.benchmark.add_question(question)
            logger.debug(f"创建新题目: {question_id}")
        else:
            # 更新题目信息（可能有变化）
            question.question = question_text
            question.choices = choices
            if category is not None:
                question.category = category

        return question

    def record_correct_answer(self, question_id: str, answer_index: int) -> None:
        """记录正确答案

        Args:
            question_id: 题目ID
            answer_index: 正确答案索引
        """
        question = self.benchmark.get_question(question_id)
        if question is None:
            raise ValueError(f"题目 {question_id} 不存在")

        question.mark_as_correct(answer_index)
        self._save_data()
        logger.info(f"题目 {question_id} 正确答案已记录: {answer_index}")

    def record_wrong_answer(self, question_id: str, answer_index: int) -> None:
        """记录错误答案

        Args:
            question_id: 题目ID
            answer_index: 错误答案索引
        """
        question = self.benchmark.get_question(question_id)
        if question is None:
            raise ValueError(f"题目 {question_id} 不存在")

        question.mark_as_wrong(answer_index)
        self._save_data()
        logger.info(f"题目 {question_id} 错误答案已记录: {answer_index}")

    def get_statistics(self) -> BenchmarkStatistics:
        """获取统计信息

        Returns:
            统计信息对象
        """
        return self.benchmark.get_statistics()

    def get_complete_questions(self) -> list[Question]:
        """获取所有完整题目

        Returns:
            完整题目列表
        """
        return self.benchmark.get_complete_questions()
