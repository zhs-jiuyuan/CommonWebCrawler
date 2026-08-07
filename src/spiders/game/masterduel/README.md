# MasterduelWebCrawler

游戏王大师决斗 (Master Duel) 卡牌数据爬虫，基于 Scrapy，采集卡牌数据与卡牌图片（数据源待定）。

## 快速开始

### 环境准备

```bash
conda activate sharecreators       # Python 3.12.0
pip install -r requirements.txt
```

### 配置

1. **Cookie**: 数据源确认后按需配置（当前为骨架，暂不需要）

2. **环境变量** (`.env`):

```env
REDIS_URL=redis://:password@localhost:6379/0
POSTGRES_URL=postgresql://user:pass@localhost/crawl_data
```

### 启动

```bash
scrapy crawl masterduel
```

## 项目结构

```
CommonWebCrawler/
├── config/
│   ├── base.py
│   └── base.yaml
├── src/
│   ├── spiders/game/masterduel/
│   │   ├── masterduel.py          # 主爬虫（开发中）
│   │   └── logs/                  # 爬虫运行日志
│   ├── pipelines/
│   │   └── postgres_pipeline.py   # PostgreSQL 入库
│   ├── middlewares/
│   │   └── curl_cffi_handler.py   # curl_cffi 下载中间件
│   └── deduplication/
│       └── redis_helper.py        # Redis 去重
├── requirements.txt
└── scrapy.cfg
```

## 当前状态

开发中，已完成：
- 基础爬虫框架搭建（继承 `BaseSpider`，target_type=game）
- 日志、限速、curl_cffi 下载中间件配置

待完成：
- 数据源调研（API/页面结构）
- 卡牌数据与卡牌图片解析
- Redis 去重与断点续爬
- 数据库入库逻辑
