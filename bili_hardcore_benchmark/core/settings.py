from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-3.5-turbo"
    openai_api_key: str = ""
    openai_timeout: int = 30

    max_questions: int = 100
    safety_threshold: int = 55

    data_dir: Path = Path("benchmark_data")
    raw_data_file: str = "questions_raw.json"
    benchmark_version: str = "v1"

    log_level: str = "INFO"
    log_file: Optional[Path] = None

    bilibili_api_timeout: int = 30

    @computed_field  # type: ignore[prop-decorator]
    @property
    def raw_data_path(self) -> Path:
        return self.data_dir / self.raw_data_file

    @computed_field  # type: ignore[prop-decorator]
    @property
    def export_dir(self) -> Path:
        return self.data_dir / f"benchmark_{self.benchmark_version}"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
