from typing import Any, Dict, Protocol

from ...core.models import Benchmark, Question


class QuestionStore(Protocol):
    def load(self) -> Dict[str, Any]: ...
    def save(self, data: Dict[str, Any]) -> None: ...


class BenchmarkService:
    def __init__(self, question_store: QuestionStore):
        self.store = question_store
        try:
            self.benchmark = Benchmark(questions=self.store.load())
        except Exception:
            self.benchmark = Benchmark()

    def save(self) -> None:
        self.store.save(self.benchmark.model_dump(mode="json")["questions"])

    def get_or_create_question(
        self, qid: str, text: str, choices: list[str], category: Optional[str] = None
    ) -> Question:
        if qid not in self.benchmark.questions:
            self.benchmark.questions[qid] = Question(
                id=qid, question=text, choices=choices, category=category
            )
        elif category and not self.benchmark.questions[qid].category:
            self.benchmark.questions[qid].category = category
        return self.benchmark.questions[qid]

    def record_attempt(self, qid: str) -> None:
        from datetime import datetime
        q = self.benchmark.questions[qid]
        q.attempts += 1
        q.last_attempt = datetime.now()
        self.save()

    def record_correct_answer(self, qid: str, idx: int) -> None:
        self.benchmark.questions[qid].correct_answer = idx
        self.record_attempt(qid)

    def record_wrong_answer(self, qid: str, idx: int) -> None:
        if idx not in self.benchmark.questions[qid].wrong_answers:
            self.benchmark.questions[qid].wrong_answers.append(idx)
        self.record_attempt(qid)

    def get_statistics(self) -> str:
        return self.benchmark.get_stats()
