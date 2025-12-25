"""依赖注入容器

使用简单的工厂模式组装所有依赖关系。
"""

from pathlib import Path

from .infrastructure.config.settings import Settings
from .infrastructure.ai.openai_provider import OpenAIProvider
from .infrastructure.bilibili.auth import BilibiliAuthClient
from .infrastructure.bilibili.user import BilibiliUserClient
from .infrastructure.bilibili.senior import BilibiliSeniorClient
from .infrastructure.persistence.question_store import JSONQuestionStore
from .infrastructure.persistence.exporters.huggingface_exporter import HuggingFaceExporter
from .infrastructure.persistence.exporters.jsonl_exporter import JSONLExporter
from .application.services.quiz_service import QuizService
from .application.services.benchmark_service import BenchmarkService
from .application.services.export_service import ExportService
from .common.logging import setup_logging


class Container:
    """依赖注入容器
    
    负责创建和管理所有服务实例。
    """
    
    def __init__(self, settings: Settings):
        """初始化容器
        
        Args:
            settings: 配置对象
        """
        self.settings = settings
        
        # 设置日志
        setup_logging(
            level=settings.log_level,
            log_file=settings.log_file
        )
        
        # 基础设施层实例（延迟初始化）
        self._ai_provider = None
        self._auth_client = None
        self._question_store = None
        self._hf_exporter = None
        self._jsonl_exporter = None
        
        # 应用层服务（延迟初始化）
        self._quiz_service = None
        self._benchmark_service = None
        self._export_service = None
    
    def get_ai_provider(self) -> OpenAIProvider:
        """获取 AI 提供者"""
        if self._ai_provider is None:
            self._ai_provider = OpenAIProvider(
                base_url=self.settings.openai_base_url,
                api_key=self.settings.openai_api_key,
                model=self.settings.openai_model,
                timeout=self.settings.openai_timeout
            )
        return self._ai_provider
    
    def get_auth_client(self) -> BilibiliAuthClient:
        """获取认证客户端"""
        if self._auth_client is None:
            self._auth_client = BilibiliAuthClient(
                timeout=self.settings.bilibili_api_timeout,
                max_retries=self.settings.bilibili_retry_times
            )
        return self._auth_client
    
    def get_user_client(self, access_token: str) -> BilibiliUserClient:
        """获取用户客户端
        
        Args:
            access_token: 访问令牌
            
        Returns:
            用户客户端实例
        """
        return BilibiliUserClient(
            access_token=access_token,
            timeout=self.settings.bilibili_api_timeout,
            max_retries=self.settings.bilibili_retry_times
        )
    
    def get_senior_client(
        self,
        access_token: str,
        csrf: str
    ) -> BilibiliSeniorClient:
        """获取答题客户端
        
        Args:
            access_token: 访问令牌
            csrf: CSRF 令牌
            
        Returns:
            答题客户端实例
        """
        return BilibiliSeniorClient(
            access_token=access_token,
            csrf=csrf,
            timeout=self.settings.bilibili_api_timeout,
            max_retries=self.settings.bilibili_retry_times
        )
    
    def get_question_store(self) -> JSONQuestionStore:
        """获取题目存储"""
        if self._question_store is None:
            self._question_store = JSONQuestionStore(
                file_path=self.settings.get_raw_data_path()
            )
        return self._question_store
    
    def get_hf_exporter(self) -> HuggingFaceExporter:
        """获取 HuggingFace 导出器"""
        if self._hf_exporter is None:
            self._hf_exporter = HuggingFaceExporter()
        return self._hf_exporter
    
    def get_jsonl_exporter(self) -> JSONLExporter:
        """获取 JSONL 导出器"""
        if self._jsonl_exporter is None:
            self._jsonl_exporter = JSONLExporter()
        return self._jsonl_exporter
    
    def get_quiz_service(self) -> QuizService:
        """获取答题服务"""
        if self._quiz_service is None:
            self._quiz_service = QuizService(
                ai_provider=self.get_ai_provider()
            )
        return self._quiz_service
    
    def get_benchmark_service(self) -> BenchmarkService:
        """获取数据收集服务"""
        if self._benchmark_service is None:
            self._benchmark_service = BenchmarkService(
                question_store=self.get_question_store()
            )
        return self._benchmark_service
    
    def get_export_service(self) -> ExportService:
        """获取导出服务"""
        if self._export_service is None:
            self._export_service = ExportService(
                hf_exporter=self.get_hf_exporter(),
                jsonl_exporter=self.get_jsonl_exporter()
            )
        return self._export_service

