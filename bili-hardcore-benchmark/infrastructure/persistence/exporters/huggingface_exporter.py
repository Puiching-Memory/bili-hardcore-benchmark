"""HuggingFace 格式导出器"""

from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from ....application.models.question import Question

from datasets import Dataset


class HuggingFaceExporter:
    """HuggingFace datasets 格式导出器
    
    导出为 Arrow 格式，适合 HuggingFace datasets 库加载。
    """
    
    def export(
        self,
        questions: list["Question"],
        output_dir: Path,
        version: str
    ) -> None:
        """导出为 HuggingFace 格式
        
        Args:
            questions: 题目列表（必须都是完整题目）
            output_dir: 输出目录
            version: 版本号
            
        Raises:
            ValueError: 如果题目列表为空或包含不完整题目
        """
        if not questions:
            raise ValueError("题目列表为空，无法导出")
        
        # 验证所有题目都是完整的
        for q in questions:
            if not q.is_complete():
                raise ValueError(f"题目 {q.id} 不完整，无法导出")
        
        # 准备数据
        data_dict = {
            "id": [],
            "question": [],
            "choices": [],
            "answer": [],
            "category": []
        }
        
        for question in questions:
            data_dict["id"].append(question.id)
            data_dict["question"].append(question.question)
            data_dict["choices"].append(question.choices)
            # correct_answer 是 0-based，直接使用
            data_dict["answer"].append(question.correct_answer)
            data_dict["category"].append(question.category or "general")
        
        # 创建 Dataset
        dataset = Dataset.from_dict(data_dict)
        
        # 添加元数据
        dataset.info.description = "Bilibili 硬核会员答题 Benchmark"
        
        # 格式化版本号为 x.y.z
        version_clean = version.lstrip('v')
        version_parts = version_clean.split('.')
        if len(version_parts) == 1:
            version_formatted = f"{version_parts[0]}.0.0"
        elif len(version_parts) == 2:
            version_formatted = f"{version_parts[0]}.{version_parts[1]}.0"
        else:
            version_formatted = version_clean
        
        dataset.info.version = version_formatted
        
        # 保存为 Arrow 格式
        output_dir.mkdir(parents=True, exist_ok=True)
        dataset.save_to_disk(str(output_dir))
        
        logger.info(
            f"已导出 {len(questions)} 道题目到 HuggingFace 格式: {output_dir}"
        )

