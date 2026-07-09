"""
测试 config/base.py 的 yaml_to_scrapy_settings 输出

用法: python3 test_config_settings.py
"""
import sys
from pathlib import Path
from types import ModuleType

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import dotenv
except ImportError:
    fake = ModuleType("dotenv")
    fake.load_dotenv = lambda *a, **kw: None
    sys.modules["dotenv"] = fake

from config.base import load_yaml_config, yaml_to_scrapy_settings


if __name__ == "__main__":
    config = load_yaml_config("base")
    settings = yaml_to_scrapy_settings(config)

    print("=" * 60)
    print("scrapy_settings 输出:")
    print("=" * 60)
    for key in sorted(settings.keys()):
        val = settings[key]
        print(f"  {key:45s} = {val}")
    print("=" * 60)
    print(f"共 {len(settings)} 项设置")

    errors = []
    checks = [
        ("BOT_NAME", "commonspider"),
        ("ROBOTSTXT_OBEY", False),
        ("SPIDER_MODULES", ["src.spiders"]),
        ("NEWSPIDER_MODULE", "src.spiders"),
        ("CONCURRENT_REQUESTS", 32),
        ("CONCURRENT_REQUESTS_PER_DOMAIN", 16),
        ("DOWNLOAD_DELAY", 2),
        ("DOWNLOAD_TIMEOUT", 30),
        ("RETRY_TIMES", 3),
        ("RETRY_HTTP_CODES", [500, 502, 503, 504, 408, 429]),
        ("LOG_LEVEL", "INFO"),
        ("LOG_FILE", "logs/scrapy.log"),
        ("AUTOTHROTTLE_ENABLED", True),
        ("AUTOTHROTTLE_DEBUG", False),
        ("HTTPCACHE_ENABLED", False),
        ("HTTPCACHE_EXPIRATION_SECS", 3600),
        ("HTTPCACHE_DIR", "httpcache"),
        ("TASK_ID_FORMAT", "{spider_name}_{date}_{timestamp}"),
        ("BATCH_SIZE", 1000),
        ("REDIS_URL", "redis://:zhs123@localhost:6379/0"),
        ("POSTGRES_URL", "postgresql://postgre:zhs123@localhost:5432/crawl_data"),
        ("REQUEST_FINGERPRINTER_IMPLEMENTATION", "2.7"),
        ("TELNETCONSOLE_ENABLED", False),
        ("ITEM_PIPELINES", {"src.pipelines.console_pipeline.ConsolePipeline": 100}),
    ]

    for key, expected in checks:
        actual = settings.get(key)
        if actual != expected:
            errors.append(f"  FAIL {key}: expected={expected!r}, got={actual!r}")

    print()
    if errors:
        print(f"失败 {len(errors)}/{len(checks)} 项:")
        for e in errors:
            print(e)
        sys.exit(1)
    else:
        print(f"全部 {len(checks)} 项检查通过!")
