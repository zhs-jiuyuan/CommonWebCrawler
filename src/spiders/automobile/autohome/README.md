# AutohomeWebCrawler

Autohome brand info crawler, based on Scrapy, collects car brand/series listing data into PostgreSQL.

## 快速开始

### 环境准备

```bash
conda activate sharecreators       # Python 3.12.0
pip install -r requirements.txt
```

### 配置

1. **Cookie**: Cookie 通过 `autohome_cookies` 模块动态获取（无需手动配置 Cookie 文件）

2. **环境变量** (`.env`):

```env
REDIS_URL=redis://:password@localhost:6379/0
POSTGRES_URL=postgresql://user:pass@localhost/crawl_data
```

### 启动

```bash
scrapy crawl autohome
```

## 项目结构

```
CommonWebCrawler/
├── config/
│   ├── base.py
│   └── base.yaml
├── src/
│   ├── spiders/automobile/autohome/
│   │   ├── autohome.py              # 主爬虫（开发中）
│   │   └── autohome_cookies/        # Cookie 获取模块
│   ├── pipelines/
│   │   └── postgres_pipeline.py     # PostgreSQL 入库
│   ├── middlewares/
│   │   └── curl_cffi_handler.py     # curl_cffi 下载中间件
│   └── deduplication/
│       └── redis_helper.py          # Redis 去重
├── requirements.txt
└── scrapy.cfg
```

## 当前状态

开发中，已完成：
- 入口 API 请求与 Cookie 获取
- 基础爬虫框架搭建

待完成：
- 品牌/车系数据解析
- Redis 去重与断点续爬
- 数据库入库逻辑
