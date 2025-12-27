"""统一日志配置

使用 loguru 提供统一的日志记录功能，支持日志级别配置、文件输出等。
"""

import sys
from pathlib import Path
from typing import Any, Optional

from loguru import logger


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    rotation: str = "10 MB",
    retention: str = "7 days",
    colorize: bool = True,
) -> None:
    """配置日志系统

    Args:
        level: 日志级别（DEBUG, INFO, WARNING, ERROR）
        log_file: 日志文件路径，如果为 None 则只输出到控制台
        rotation: 日志文件轮转策略
        retention: 日志文件保留时间
        colorize: 是否启用彩色输出
    """
    # 移除默认的 handler
    logger.remove()

    # 添加控制台输出
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>",
        colorize=colorize,
    )

    # 如果指定了日志文件，添加文件输出
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            str(log_file),
            level=level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
            "{name}:{function}:{line} | {message}",
            rotation=rotation,
            retention=retention,
            encoding="utf-8",
        )

    logger.info(f"日志系统已初始化，级别: {level}")


def get_logger(name: str) -> Any:
    """获取指定名称的 logger

    Args:
        name: logger 名称，通常使用 __name__

    Returns:
        logger 实例
    """
    return logger.bind(name=name)
