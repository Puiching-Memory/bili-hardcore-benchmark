from loguru import logger

from .container import Container
from .core.settings import get_settings


def main() -> None:
    try:
        settings = get_settings()
        container = Container(settings)
        benchmark = container.benchmark_service.benchmark

        if not benchmark.questions:
            logger.warning("No data to export")
            return

        export = container.export_service
        export.export_huggingface(benchmark, settings.export_dir, settings.benchmark_version, True)
        export.export_jsonl(
            benchmark, settings.data_dir / f"benchmark_{settings.benchmark_version}.jsonl"
        )
        logger.info("Export complete")
    except Exception as e:
        logger.error(e)


if __name__ == "__main__":
    main()
