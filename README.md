# CommonWebCrawler

通用多平台数据采集框架，基于 Scrapy 2.16，支持社交媒体、汽车、财经新闻等多类别数据的自动化采集，统一存入 PostgreSQL，通过 Redis 实现去重与断点续爬。

## 支持的平台

| 类别 | 平台 | 爬虫命令 | 状态 |
|------|------|----------|------|
| 社交媒体 | 小红书 | `scrapy crawl xiaohongshu` | 完成 |
| 汽车 | 汽车之家 | `scrapy crawl autohome` | 进行中 |
| 财经新闻 | 财联社 | — | 规划中 |

## 技术栈

| 组件 | 用途 |
|------|------|
| Scrapy 2.16 | 爬虫框架 |
| curl_cffi | TLS 指纹伪装（模拟 Chrome/Safari） |
| Redis | 全局去重 + 断点续爬 + 进度追踪 |
| PostgreSQL | 统一数据持久化存储 |
| PyYAML | 配置文件解析 |
| python-dotenv | 环境变量管理 |

### 平台专属依赖

| 平台 | 依赖 | 说明 |
|------|------|------|
| 小红书 | xhshow | x-s/x-t 接口签名纯算法库，无需浏览器 |
| 汽车之家 | cloakbrowser | 无头浏览器获取认证 Cookie |

## 快速开始

### 环境准备

```bash
conda activate spider          # Python 3.12.0
pip install -r requirements.txt
```

### 配置

1. **Cookie 配置**：将平台登录后的 Cookie 放入各爬虫目录的 Cookie 文件（如 `src/spiders/socialmedia/xhs/xhs_cookies.json`）

2. **环境变量** (复制 `.env.example` 为 `.env`)：

```env
POSTGRES_URL=postgresql://user:password@localhost:5432/crawl_data
REDIS_URL=redis://:password@localhost:6379/0
LOG_LEVEL=INFO
LOG_FILE=logs/scrapy.log
# PROXY_API_URL=http://localhost:5010/get  # 可选
# PROXY_ENABLED=false                      # 可选
```

3. **全局配置** (`config/base.yaml`)：

集中管理并发数、下载延迟、自动限速、重试策略等通用参数，支持 `${VAR:default}` 环境变量注入。

### 启动

```bash
# 小红书 — 全量采集
scrapy crawl xiaohongshu

# 小红书 — 增量采集
scrapy crawl xiaohongshu -a mode=incremental -a incre_num=5

# 小红书 — 指定关键词 + 数量
scrapy crawl xiaohongshu -a keyword=美食 -a num=10

# 汽车之家
scrapy crawl autohome
```

## 项目结构

```
CommonWebCrawler/
├── config/
│   ├── base.py                 # Scrapy settings 加载（YAML → 环境变量注入）
│   └── base.yaml               # 全局配置（并发、延迟、重试等）
├── src/
│   ├── spiders/
│   │   ├── base.py             # 爬虫基类（Item 创建、校验、统计摘要）
│   │   ├── socialmedia/        # 社交媒体分类
│   │   │   └── xhs/
│   │   │       ├── xiaohongshu.py    # 小红书爬虫（搜索 → 详情 → 入库）
│   │   │       ├── xhs_config.py     # 爬取参数配置
│   │   │       ├── xhs_sign.py       # 接口签名（xhshow 封装）
│   │   │       ├── incremental-design.md  # 增量采集设计文档
│   │   │       └── xhs_cookies.json       # Cookie（已 gitignore）
│   │   ├── automobile/         # 汽车分类
│   │   │   └── autohome/
│   │   │       ├── autohome.py       # 汽车之家爬虫
│   │   │       └── autohome_cookies/ # Cookie 获取模块
│   │   └── financialnews/      # 财经新闻分类（规划中）
│   │       └── cls/            # 财联社（待实现）
│   ├── pipelines/
│   │   ├── postgres_pipeline.py # PostgreSQL 入库（ON CONFLICT 去重）
│   │   └── console_pipeline.py  # 控制台输出（调试用）
│   ├── middlewares/
│   │   └── curl_cffi_handler.py # curl_cffi 下载中间件
│   ├── items/
│   │   └── base.py             # Item 基类（字段定义 + 校验）
│   └── deduplication/
│       └── redis_helper.py     # Redis 去重 + 进度追踪
├── requirements.txt
└── scrapy.cfg
```

## 架构设计

### 爬虫类层次

```
scrapy.Spider
  └── BaseSpider                 ← 通用能力：创建 Item、字段校验、关闭统计
        ├── SocialMediaSpider    ← target_type = "socialmedia"
        │     └── XiaohongshuSpider
        ├── AutomobileSpider     ← target_type = "automobile"
        │     └── AutohomeSpider
        └── FinancialNewsSpider  ← target_type = "financialnews"
              └── (待实现)
```

`BaseSpider` 封装了 Item 创建和自动校验逻辑，子类只需设置 `target_type` 即可确定数据归属类别。每个平台爬虫独立管理自己的 Cookie、签名和解析逻辑。

### 数据流

1. **发起请求** — `curl_cffi` 中间件替换 Scrapy 默认下载器，实现 TLS 指纹伪装，规避反爬检测
2. **解析数据** — 各平台爬虫调用 API 并解析响应
3. **去重检查** — Redis SET 进行全局 URL 去重
4. **Item 校验** — `BaseItem.validate()` 确保必填字段非空
5. **入库** — `PostgresPipeline` 写入 PostgreSQL，`ON CONFLICT DO NOTHING` 防重复

### 数据库表

表 `public.social_media` 以 `(platform, data_type, item_id)` 作为唯一约束，字段包括 `title`、`content`、`author`、`like_count`、`comment_count`、`share_count`、`raw_data` 等，支持多平台数据汇总。

## 添加新平台

1. 在 `src/spiders/<category>/` 下创建平台子目录
2. 继承对应分类基类（`SocialMediaSpider` / `AutomobileSpider` / `FinancialNewsSpider`）
3. 实现 API 请求、数据解析和 Item 构造逻辑
4. 如需特殊签名或 Cookie，在子目录内独立管理

## 小红书详情

### 采集模式

| 模式 | 命令参数 | 说明 |
|------|----------|------|
| 全量 | `(默认)` | 遍历关键词，每个采 `MAX_NOTES_COUNT` 条 |
| 增量 | `-a mode=incremental -a incre_num=5` | 按轮推进，每轮每个关键词采固定条新笔记 |
| 指定 | `-a keyword=美食 -a num=10` | 指定单个关键词和采集数量 |

### 反爬签名

使用 `xhshow` 纯算法库生成 x-s、x-t、x-s-common、x-b3-traceid 等请求签名，配合 `curl_cffi` 的 TLS 指纹伪装浏览器环境，无需 Playwright 等浏览器方案。

### 增量机制

增量模式以**轮**为推进单位，每轮每个关键词各采集 `incre_num` 条新笔记，全部关键词完成才推进到下一轮。全量模式与增量模式共用同一个去重 SET，天然互不重复。

详见 `src/spiders/socialmedia/xhs/incremental-design.md`。

### Redis Key 结构

```
{xiaohongshu}:notes              SET    "url|search"            全局去重
{xiaohongshu}:kw:{keyword}       HASH   {target, done}          关键词状态
{xiaohongshu}:kw:{keyword}:cnt   STRING                         已采集计数
{xiaohongshu}:incr:kw:{keyword}  HASH   {target, done}          增量关键词状态
{xiaohongshu}:incr:kw:{keyword}:cnt STRING                       增量已采集计数
```
