"""配置管理

使用 Pydantic Settings 实现类型安全的配置管理，支持环境变量和默认值。
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置

    所有配置项都可以通过环境变量覆盖（大写形式）。
    例如：OPENAI_API_KEY 环境变量会覆盖 openai_api_key 配置。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # OpenAI 配置
    openai_base_url: str = Field(
        default="https://api.openai.com/v1", description="OpenAI API base URL"
    )
    openai_model: str = Field(default="gpt-3.5-turbo", description="OpenAI 模型名称")
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    openai_timeout: int = Field(default=30, description="OpenAI API 超时时间（秒）")

    # 答题配置
    max_questions: int = Field(default=100, description="单次会话最大答题数")
    safety_threshold: int = Field(
        default=55, description="安全阈值，达到此分数后停止答题（避免通过60分）"
    )

    # 数据存储配置
    data_dir: Path = Field(default=Path("benchmark_data"), description="数据存储目录")
    raw_data_file: str = Field(default="questions_raw.json", description="原始数据文件名")
    benchmark_version: str = Field(default="v1", description="基准测试版本")

    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别（DEBUG, INFO, WARNING, ERROR）")
    log_file: Optional[Path] = Field(
        default=None, description="日志文件路径，None 表示只输出到控制台"
    )

    # B站 API 配置
    bilibili_api_timeout: int = Field(default=30, description="B站 API 超时时间（秒）")
    bilibili_retry_times: int = Field(default=3, description="B站 API 重试次数")

    def get_raw_data_path(self) -> Path:
        """获取原始数据文件完整路径"""
        return self.data_dir / self.raw_data_file

    def get_export_dir(self) -> Path:
        """获取导出目录路径"""
        return self.data_dir / f"benchmark_{self.benchmark_version}"

    def get_export_jsonl_path(self) -> Path:
        """获取 JSONL 导出文件路径"""
        return self.data_dir / f"benchmark_{self.benchmark_version}.jsonl"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例

    使用 lru_cache 确保配置对象只创建一次。

    Returns:
        Settings 实例
    """
    return Settings()
