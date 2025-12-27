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
        version: str,
        split_by_category: bool = False
    ) -> BenchmarkStatistics:
        """导出为 HuggingFace 格式
        
        只导出完整题目（已知正确答案）。
        
        Args:
            benchmark: 基准测试实例
            output_dir: 输出目录
            version: 版本号
            split_by_category: 是否按分类导出子数据集
            
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
        
        if split_by_category:
            # 按分类分组
            from collections import defaultdict
            questions_by_category = defaultdict(list)
            for q in complete_questions:
                category = q.category or "未分类"
                questions_by_category[category].append(q)
            
            logger.info(f"准备按分类导出 {len(complete_questions)} 道完整题目，共 {len(questions_by_category)} 个分类")
            
            # 为每个分类导出子数据集
            # 分类名称映射（用于文件路径）
            category_name_map = {
                "体育": "体育",
                "文史": "文史",
                "知识": "知识",
                "动画/漫画": "动画_漫画",
                "影视": "影视",
                "游戏": "游戏",
                "音乐": "音乐",
                "鬼畜": "鬼畜"
            }
            
            for category, cat_questions in questions_by_category.items():
                # 使用映射后的分类名称，用于文件路径
                safe_category = category_name_map.get(category, category.replace("/", "_").replace("\\", "_"))
                cat_output_dir = output_dir / safe_category
                
                try:
                    self.hf_exporter.export(cat_questions, cat_output_dir, version)
                    logger.info(f"✅ {category}: {len(cat_questions)} 道题目已导出到 {cat_output_dir}")
                except Exception as e:
                    logger.error(f"❌ 导出分类 {category} 失败: {e}")
                    raise
        else:
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

