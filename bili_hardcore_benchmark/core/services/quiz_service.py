import random
from typing import Optional, Protocol

from ...core.models import Question


class AIProvider(Protocol):
    def predict(self, question: str, choices: list[str]) -> int: ...


class QuizService:
    def __init__(self, ai_provider: AIProvider):
        self.ai_provider = ai_provider

    def select_answer(self, q: Question) -> tuple[int, str]:
        if q.correct_answer is not None:
            wrong = [i for i in range(len(q.choices)) if i != q.correct_answer]
            return random.choice(wrong or [0]), "故意选错"

        untried = q.get_untried_indices()
        if len(untried) == 1:
            return untried[0], "排除法"

        ai_idx = self.ai_provider.predict(q.question, [q.choices[i] for i in untried])
        return untried[ai_idx], "AI推荐"

    def should_skip_question(self, q: Question, score: int, threshold: int) -> bool:
        return q.correct_answer is not None and score < threshold

    def judge_result(
        self, q: Question, idx: int, old_score: int, new_score: int
    ) -> tuple[bool, Optional[int]]:
        if new_score > old_score:
            return True, idx
        if len(q.choices) == 2:
            return False, 1 - idx
        return False, None
