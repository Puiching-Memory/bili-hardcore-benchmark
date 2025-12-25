"""公共类型定义

定义项目中使用的通用类型、协议和类型别名。
"""

from typing import Protocol, TypedDict, Any


class QuestionDict(TypedDict, total=False):
    """题目数据字典类型"""
    id: str
    question: str
    choices: list[str]
    correct_answer: int | None
    wrong_answers: list[int]
    category: str | None
    attempts: int
    last_attempt: str


class APIResponse(TypedDict):
    """API 响应类型"""
    code: int
    message: str
    data: dict[str, Any] | None


class BenchmarkStats(TypedDict):
    """基准测试统计信息类型"""
    total_questions: int
    complete_questions: int
    partial_questions: int
    unknown_questions: int
    completion_rate: float


class AIProvider(Protocol):
    """AI 提供者协议"""
    
    def predict(self, question: str, choices: list[str]) -> int:
        """预测答案
        
        Args:
            question: 题目内容
            choices: 选项列表
            
        Returns:
            预测的答案索引（0-based）
        """
        ...


class QuestionStore(Protocol):
    """题目存储协议"""
    
    def load(self) -> dict[str, QuestionDict]:
        """加载所有题目"""
        ...
    
    def save(self, questions: dict[str, QuestionDict]) -> None:
        """保存所有题目"""
        ...
    
    def get_question(self, question_id: str) -> QuestionDict | None:
        """获取单个题目"""
        ...
    
    def update_question(self, question_id: str, question: QuestionDict) -> None:
        """更新单个题目"""
        ...

