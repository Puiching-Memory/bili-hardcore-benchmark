from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar, cast

from pydantic import BaseModel, Field

T = TypeVar("T")


class QuestionStatus(str, Enum):
    UNKNOWN = "unknown"
    PARTIAL = "partial"
    COMPLETE = "complete"


class Question(BaseModel):
    id: str
    question: str
    choices: List[str]
    category: Optional[str] = None
    correct_answer: Optional[int] = None
    wrong_answers: List[int] = Field(default_factory=list)
    attempts: int = 0
    last_attempt: Optional[datetime] = None

    @property
    def status(self) -> QuestionStatus:
        if self.correct_answer is not None:
            return QuestionStatus.COMPLETE
        return QuestionStatus.PARTIAL if self.wrong_answers else QuestionStatus.UNKNOWN

    @property
    def is_complete(self) -> bool:
        return self.correct_answer is not None

    def get_untried_indices(self) -> List[int]:
        if self.correct_answer is not None:
            return []
        return [i for i in range(len(self.choices)) if i not in self.wrong_answers]


class BiliResponse(BaseModel, Generic[T]):
    code: int
    message: str = ""
    data: Optional[T] = None

    @property
    def is_success(self) -> bool:
        return self.code == 0


class QRCodeData(BaseModel):
    url: str
    auth_code: str


class LoginData(BaseModel):
    access_token: str
    mid: int
    cookie_info: Dict[str, Any] = Field(default_factory=dict)

    @property
    def csrf(self) -> Optional[str]:
        for c in self.cookie_info.get("cookies", []):
            if c.get("name") == "bili_jct":
                return cast(Optional[str], c.get("value"))
        return None


class BiliAnswer(BaseModel):
    ans_text: str
    ans_hash: str


class BiliQuestion(BaseModel):
    id: int
    question: str
    answers: List[BiliAnswer]
    question_num: int

    @property
    def choices(self) -> List[str] :
        return [a.ans_text for a in self.answers]


class BiliCategoryScore(BaseModel):
    category: str
    score: int
    total: int


class BiliResult(BaseModel):
    score: int
    scores: List[BiliCategoryScore] = Field(default_factory=list)


class Benchmark(BaseModel):
    questions: Dict[str, Question] = Field(default_factory=dict)

    def get_stats(self) -> str:
        total = len(self.questions)
        complete = sum(
            1 for q in self.questions.values() if q.correct_answer is not None
        )
        return (
            f"Total: {total}, Complete: {complete} ({complete/total*100:.1f}%)"
            if total
            else "No data"
        )
