"""数据导出服务

负责将中间格式的数据导出为 HuggingFace 格式。
"""

from pathlib import Path
from typing import Protocol
from loguru import logger

from ..models.question import Question
from ..models.benchmark import Benchmark, BenchmarkStatistics


class HuggingFaceExporter(Protocol):
    """HuggingFace 导出器协议"""
    
    def export(
        self,
        questions: list[Question],
        output_dir: Path,
        version: str
    ) -> None:
        """导出为 HuggingFace 格式
        
        Args:
            questions: 题目列表
            output_dir: 输出目录
            version: 版本号
        """
        ...


class JSONLExporter(Protocol):
    """JSONL 导出器协议"""
    
    def export(
        self,
        questions: list[Question],
        output_file: Path
    ) -> None:
        """导出为 JSONL 格式
        
        Args:
            questions: 题目列表
            output_file: 输出文件路径
        """
        ...


class ExportService:
    """数据导出服务
    
    从 Benchmark 中提取完整题目并导出为指定格式。
    """
    
    def __init__(
        self,
        hf_exporter: HuggingFaceExporter,
        jsonl_exporter: JSONLExporter
    ):
        """初始化导出服务
        
        Args:
            hf_exporter: HuggingFace 导出器
            jsonl_exporter: JSONL 导出器
        """
        self.hf_exporter = hf_exporter
        self.jsonl_exporter = jsonl_exporter
    
    def export_huggingface(
        self,
        benchmark: Benchmark,
        output_dir: Path,
        version: str
    ) -> BenchmarkStatistics:
        """导出为 HuggingFace 格式
        
        只导出完整题目（已知正确答案）。
        
        Args:
            benchmark: 基准测试实例
            output_dir: 输出目录
            version: 版本号
            
        Returns:
            导出题目的统计信息
        """
        complete_questions = benchmark.get_complete_questions()
        
        if not complete_questions:
            logger.warning("没有完整题目可以导出")
            return BenchmarkStatistics(
                total_questions=0,
                complete_questions=0,
                partial_questions=0,
                unknown_questions=0,
                completion_rate=0.0
            )
        
        logger.info(f"准备导出 {len(complete_questions)} 道完整题目")
        
        try:
            self.hf_exporter.export(complete_questions, output_dir, version)
            logger.info(f"HuggingFace 格式已导出到: {output_dir}")
        except Exception as e:
            logger.error(f"导出 HuggingFace 格式失败: {e}")
            raise
        
        # 返回导出题目的统计信息
        stats = benchmark.get_statistics()
        return stats
    
    def export_jsonl(
        self,
        benchmark: Benchmark,
        output_file: Path
    ) -> BenchmarkStatistics:
        """导出为 JSONL 格式
        
        只导出完整题目（已知正确答案）。
        
        Args:
            benchmark: 基准测试实例
            output_file: 输出文件路径
            
        Returns:
            导出题目的统计信息
        """
        complete_questions = benchmark.get_complete_questions()
        
        if not complete_questions:
            logger.warning("没有完整题目可以导出")
            return BenchmarkStatistics(
                total_questions=0,
                complete_questions=0,
                partial_questions=0,
                unknown_questions=0,
                completion_rate=0.0
            )
        
        logger.info(f"准备导出 {len(complete_questions)} 道完整题目")
        
        try:
            self.jsonl_exporter.export(complete_questions, output_file)
            logger.info(f"JSONL 格式已导出到: {output_file}")
        except Exception as e:
            logger.error(f"导出 JSONL 格式失败: {e}")
            raise
        
        # 返回导出题目的统计信息
        stats = benchmark.get_statistics()
        return stats

