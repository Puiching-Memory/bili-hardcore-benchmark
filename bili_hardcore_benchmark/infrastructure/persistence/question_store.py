import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, cast


class JSONQuestionStore:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        if not self.file_path.exists():
            return {}
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return cast(Dict[str, Any], data.get("questions", {}))
            return {}

    def save(self, questions: Dict[str, Any]) -> None:
        data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "questions": questions,
        }
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
