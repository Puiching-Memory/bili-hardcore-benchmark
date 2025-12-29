"""JSONL 格式导出器"""

import json
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from ....core.models import Question


class JSONLExporter:
    """JSONL 格式导出器

    每行一个 JSON 对象，适合流式处理和大规模数据集。
    """

    def export(self, questions: list["Question"], output_file: Path) -> None:
        """导出为 JSONL 格式

        Args:
            questions: 题目列表（必须都是完整题目）
            output_file: 输出文件路径

        Raises:
            ValueError: 如果题目列表为空或包含不完整题目
        """
        if not questions:
            raise ValueError("题目列表为空，无法导出")

        # 验证所有题目都是完整的
        for q in questions:
            if not q.is_complete:
                raise ValueError(f"题目 {q.id} 不完整，无法导出")

        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 写入 JSONL
        with open(output_file, "w", encoding="utf-8") as f:
            for question in questions:
                record = {
                    "id": question.id,
                    "question": question.question,
                    "choices": question.choices,
                    "answer": question.correct_answer,  # 0-based
                    "category": question.category or "general",
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        logger.info(f"已导出 {len(questions)} 道题目到 JSONL 格式: {output_file}")
