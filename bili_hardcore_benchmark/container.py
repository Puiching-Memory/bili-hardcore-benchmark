from functools import cached_property

from .core.logging import setup_logging
from .core.services.auth_service import AuthService
from .core.services.benchmark_service import BenchmarkService
from .core.services.export_service import ExportService
from .core.services.quiz_service import QuizService
from .core.settings import Settings
from .infrastructure.ai.openai_provider import OpenAIProvider
from .infrastructure.bilibili.auth import BilibiliAuthClient
from .infrastructure.bilibili.senior import BilibiliSeniorClient
from .infrastructure.bilibili.user import BilibiliUserClient
from .infrastructure.persistence.exporters.huggingface_exporter import HuggingFaceExporter
from .infrastructure.persistence.exporters.jsonl_exporter import JSONLExporter
from .infrastructure.persistence.question_store import JSONQuestionStore


class Container:
    def __init__(self, settings: Settings):
        self.settings = settings
        setup_logging(level=settings.log_level, log_file=settings.log_file)

    @cached_property
    def auth_service(self) -> AuthService:
        return AuthService(auth_client=self.auth_client)

    @cached_property
    def ai_provider(self) -> OpenAIProvider:
        return OpenAIProvider(
            base_url=self.settings.openai_base_url,
            api_key=self.settings.openai_api_key,
            model=self.settings.openai_model,
            timeout=self.settings.openai_timeout,
        )

    @cached_property
    def auth_client(self) -> BilibiliAuthClient:
        return BilibiliAuthClient(timeout=self.settings.bilibili_api_timeout)

    def get_user_client(self, access_token: str) -> BilibiliUserClient:
        return BilibiliUserClient(
            access_token=access_token, timeout=self.settings.bilibili_api_timeout
        )

    def get_senior_client(self, access_token: str, csrf: str) -> BilibiliSeniorClient:
        return BilibiliSeniorClient(
            access_token=access_token, csrf=csrf, timeout=self.settings.bilibili_api_timeout
        )

    @cached_property
    def question_store(self) -> JSONQuestionStore:
        return JSONQuestionStore(file_path=self.settings.raw_data_path)

    @cached_property
    def quiz_service(self) -> QuizService:
        return QuizService(ai_provider=self.ai_provider)

    @cached_property
    def benchmark_service(self) -> BenchmarkService:
        return BenchmarkService(question_store=self.question_store)

    @cached_property
    def export_service(self) -> ExportService:
        return ExportService(hf_exporter=HuggingFaceExporter(), jsonl_exporter=JSONLExporter())
