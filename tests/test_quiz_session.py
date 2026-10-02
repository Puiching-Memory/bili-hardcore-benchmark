"""Offline regression tests: real collector code, fixed-order API fixtures."""

import json
import socket
import unittest
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from bili_hardcore_benchmark import main as collector
from bili_hardcore_benchmark.container import Container
from bili_hardcore_benchmark.core.exceptions import APIError
from bili_hardcore_benchmark.core.models import (
    BiliAnswer,
    BiliCategoryScore,
    BiliQuestion,
    BiliResult,
    LoginData,
    Question,
)
from bili_hardcore_benchmark.core.services.quiz_service import QuizService
from bili_hardcore_benchmark.core.settings import Settings


class FixedPredictor:
    def __init__(self) -> None:
        self.calls = 0

    def predict(self, question: str, choices: list[str]) -> int:
        self.calls += 1
        return 0


@dataclass
class Submission:
    qid: str
    chosen_idx: int
    correct: bool
    score_before: int


class OfflineSenior:
    def __init__(self, questions: list[tuple[str, int]], score: int = 0) -> None:
        self.questions = questions
        self.score = score
        self.submissions: list[Submission] = []
        self.result_query_positions: list[int] = []
        self.submission_attempts = 0
        self.fail_submit = False
        self.fail_result_after_submit = False

    @staticmethod
    def choices(qid: str) -> list[str]:
        return [f"question {qid}: option {idx}" for idx in range(4)]

    def get_result(self) -> BiliResult:
        self.result_query_positions.append(len(self.submissions))
        if self.fail_result_after_submit and self.submissions:
            raise APIError("offline result query failure")
        return BiliResult(
            score=self.score,
            scores=[BiliCategoryScore(category="offline", score=self.score, total=100)],
        )

    def get_question(self) -> BiliQuestion:
        position = len(self.submissions)
        qid, _ = self.questions[position]
        return BiliQuestion(
            id=int(qid),
            question=f"offline question {qid}",
            answers=[
                BiliAnswer(ans_text=text, ans_hash=f"offline-{qid}-{idx}")
                for idx, text in enumerate(self.choices(qid))
            ],
            question_num=position + 1,
        )

    def submit_answer(self, qid: int, ans_hash: str, ans_text: str) -> dict:
        self.submission_attempts += 1
        if self.fail_submit:
            raise APIError("offline submission failure")
        current_qid, correct_idx = self.questions[len(self.submissions)]
        if str(qid) != current_qid:
            raise AssertionError("Submitted question does not match the fixture")
        hashes = [f"offline-{current_qid}-{idx}" for idx in range(4)]
        chosen_idx = hashes.index(ans_hash)
        if ans_text != self.choices(current_qid)[chosen_idx]:
            raise AssertionError("Answer text and hash do not match")
        correct = chosen_idx == correct_idx
        self.submissions.append(Submission(current_qid, chosen_idx, correct, self.score))
        if correct:
            self.score += 1
        return {}


class QuizSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        task_dir = TemporaryDirectory(prefix="bili-offline-regression-")
        self.addCleanup(task_dir.cleanup)
        settings = Settings(_env_file=None, data_dir=Path(task_dir.name), log_level="ERROR")
        self.container = Container(settings)
        self.predictor = FixedPredictor()
        self.container.ai_provider = self.predictor
        self.login = LoginData(
            access_token="offline-fixture",
            mid=0,
            cookie_info={"cookies": [{"name": "bili_jct", "value": "offline-fixture"}]},
        )

    def seed_known(self, qid: str, correct_idx: int, wrong_indices: list[int]) -> Question:
        question = Question(
            id=qid,
            question=f"offline question {qid}",
            choices=OfflineSenior.choices(qid),
            correct_answer=correct_idx,
            wrong_answers=wrong_indices,
        )
        self.container.benchmark_service.benchmark.questions[qid] = question
        return question

    def run_session(self, senior: OfflineSenior) -> None:
        self.container.settings.max_questions = len(senior.questions)
        with (
            patch.object(self.container, "get_senior_client", return_value=senior),
            patch.object(collector.time, "sleep", return_value=None),
            patch.object(socket.socket, "connect", side_effect=AssertionError("Network forbidden")),
        ):
            collector.run_quiz(self.container, self.login)

    def stored_question(self, qid: str) -> dict:
        data = json.loads(self.container.settings.raw_data_path.read_text(encoding="utf-8"))
        return data["questions"][qid]

    def test_selector_excludes_known_first_answer_without_wrong_history(self) -> None:
        question = self.seed_known("101", 0, [])
        idx, _ = QuizService(self.predictor).select_answer(question)
        self.assertIn(idx, [1, 2, 3])
        self.assertEqual(self.predictor.calls, 0)

    def test_loop_excludes_every_known_correct_index_and_checks_result(self) -> None:
        for correct_idx in range(4):
            with self.subTest(correct_idx=correct_idx):
                qid = str(101 + correct_idx)
                self.seed_known(qid, correct_idx, [])
                senior = OfflineSenior([(qid, correct_idx)])
                self.run_session(senior)
                self.assertFalse(senior.submissions[0].correct)
                self.assertEqual(senior.result_query_positions, [0, 1])
                stored = self.stored_question(qid)
                self.assertEqual(stored["correct_answer"], correct_idx)
                self.assertEqual(stored["attempts"], 1)
                self.assertEqual(self.predictor.calls, 0)

    def test_next_wrong_answer_is_not_persisted_as_correct(self) -> None:
        self.seed_known("101", 0, [])
        senior = OfflineSenior([("101", 0), ("102", 1)])
        self.run_session(senior)
        self.assertFalse(senior.submissions[1].correct)
        self.assertIsNone(self.stored_question("102")["correct_answer"])
        self.assertEqual(self.stored_question("102")["wrong_answers"], [0])
        self.assertEqual(senior.result_query_positions, [0, 1, 2])

    def test_known_wrong_history_preserves_next_wrong_label(self) -> None:
        self.seed_known("101", 0, [1])
        senior = OfflineSenior([("101", 0), ("102", 1)])
        self.run_session(senior)
        self.assertFalse(senior.submissions[0].correct)
        self.assertIsNone(self.stored_question("102")["correct_answer"])
        self.assertEqual(self.stored_question("102")["wrong_answers"], [0])

    def test_unknown_correct_answer_is_persisted_with_category(self) -> None:
        senior = OfflineSenior([("102", 0)])
        self.run_session(senior)
        stored = self.stored_question("102")
        self.assertEqual(stored["correct_answer"], 0)
        self.assertEqual(stored["category"], "offline")
        self.assertEqual(stored["attempts"], 1)
        self.assertEqual(senior.score, 1)

    def test_unknown_wrong_answer_is_persisted_as_wrong(self) -> None:
        senior = OfflineSenior([("102", 1)])
        self.run_session(senior)
        self.assertIsNone(self.stored_question("102")["correct_answer"])
        self.assertEqual(self.stored_question("102")["wrong_answers"], [0])
        self.assertEqual(senior.score, 0)

    def test_threshold_uses_latest_score_before_another_submission(self) -> None:
        self.seed_known("101", 0, [])
        senior = OfflineSenior([("101", 0), ("102", 0), ("103", 0)], score=54)
        self.run_session(senior)
        self.assertTrue(all(s.score_before < 55 for s in senior.submissions))
        self.assertEqual(senior.score, 55)
        self.assertEqual(len(senior.submissions), 2)

    def test_existing_threshold_stops_before_submission(self) -> None:
        senior = OfflineSenior([("101", 0)], score=55)
        self.run_session(senior)
        self.assertEqual(senior.submission_attempts, 0)

    def test_failed_submission_does_not_persist_a_label(self) -> None:
        senior = OfflineSenior([("101", 0)])
        senior.fail_submit = True
        self.run_session(senior)
        self.assertEqual(senior.submission_attempts, 1)
        self.assertEqual(senior.result_query_positions, [0])
        self.assertFalse(self.container.settings.raw_data_path.exists())

    def test_failed_result_query_does_not_record_a_known_attempt(self) -> None:
        question = self.seed_known("101", 0, [])
        senior = OfflineSenior([("101", 0)])
        senior.fail_result_after_submit = True
        self.run_session(senior)
        self.assertEqual(question.attempts, 0)
        self.assertEqual(question.wrong_answers, [])
        self.assertEqual(senior.result_query_positions, [0, 1])
        self.assertFalse(self.container.settings.raw_data_path.exists())


if __name__ == "__main__":
    unittest.main()
