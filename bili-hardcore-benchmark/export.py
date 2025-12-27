"""导出脚本 - 独立运行

从中间格式读取数据，导出为 HuggingFace 格式。
"""

import sys

from loguru import logger

from .container import Container
from .infrastructure.config.settings import get_settings
from .common.exceptions import BiliHardcoreError, DataError


def main() -> None:
    """主函数"""
    try:
        # 加载配置
        settings = get_settings()
        container = Container(settings)
        
        logger.info("=" * 50)
        logger.info("Bili-Hardcore-Benchmark - 导出模式")
        logger.info("=" * 50)
        
        # 加载数据
        logger.info(f"正在从 {settings.get_raw_data_path()} 加载数据...")
        benchmark_service = container.get_benchmark_service()
        
        # 获取统计信息
        stats = benchmark_service.get_statistics()
        logger.info("\n数据统计:")
        logger.info(f"{stats}")
        
        if stats.complete_questions == 0:
            logger.warning("\n⚠️  没有完整题目可以导出")
            logger.info("请先运行 'uv run python -m bili-hardcore.main' 收集题目数据")
            sys.exit(0)
        
        # 导出 HuggingFace 格式
        logger.info(f"\n正在导出 {stats.complete_questions} 道完整题目...")
        export_service = container.get_export_service()
        
        # 导出 Arrow 格式（按分类导出子数据集）
        export_dir = settings.get_export_dir()
        export_service.export_huggingface(
            benchmark=benchmark_service.benchmark,
            output_dir=export_dir,
            version=settings.benchmark_version,
            split_by_category=True  # 按分类导出
        )
        logger.info(f"✅ HuggingFace 格式（按分类）已导出到: {export_dir}")
        
        # 导出 JSONL 格式
        jsonl_file = settings.get_export_jsonl_path()
        export_service.export_jsonl(
            benchmark=benchmark_service.benchmark,
            output_file=jsonl_file
        )
        logger.info(f"✅ JSONL 格式已导出到: {jsonl_file}")
        
        logger.info("\n" + "=" * 50)
        logger.info("导出完成！")
        logger.info("=" * 50)
        
        logger.info("\n使用方式:")
        logger.info("  # 方法1: 加载 Arrow 格式（推荐，速度快）")
        logger.info(f"  from datasets import load_from_disk")
        logger.info(f"  dataset = load_from_disk('{export_dir}')")
        logger.info("")
        logger.info("  # 方法2: 加载 JSONL 格式（兼容性好）")
        logger.info(f"  from datasets import load_dataset")
        logger.info(f"  dataset = load_dataset('json', data_files='{jsonl_file}')")
        
    except FileNotFoundError:
        logger.error("❌ 未找到数据文件")
        logger.info("请先运行 'uv run python -m bili-hardcore.main' 收集题目数据")
        sys.exit(1)
    except DataError as e:
        logger.error(f"❌ 数据错误: {e}")
        sys.exit(1)
    except BiliHardcoreError as e:
        logger.error(f"❌ {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n程序已中断")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"❌ 未预期的错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

