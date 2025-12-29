from pathlib import Path
from typing import Protocol

from ...core.models import Benchmark, Question


class HuggingFaceExporter(Protocol):
    def export(self, questions: list[Question], output_dir: Path, version: str) -> None: ...


class JSONLExporter(Protocol):
    def export(self, questions: list[Question], output_file: Path) -> None: ...


class ExportService:
    def __init__(self, hf_exporter: HuggingFaceExporter, jsonl_exporter: JSONLExporter):
        self.hf_exporter, self.jsonl_exporter = hf_exporter, jsonl_exporter

    def export_huggingface(
        self, benchmark: Benchmark, output_dir: Path, version: str, split: bool = False
    ) -> None:
        qs = [q for q in benchmark.questions.values() if q.correct_answer is not None]
        if not qs:
            return
        self.hf_exporter.export(qs, output_dir, version)

    def export_jsonl(self, benchmark: Benchmark, output_file: Path) -> None:
        qs = [q for q in benchmark.questions.values() if q.correct_answer is not None]
        if not qs:
            return
        self.jsonl_exporter.export(qs, output_file)
