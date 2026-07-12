# XHSWebCrawler

小红书搜索爬虫，基于 Scrapy 2.16，根据关键词搜索采集笔记详情，存入 PostgreSQL，并通过 Redis 做去重和断点续爬。

## 技术栈

| 组件 | 用途 |
|------|------|
| Scrapy 2.16 | 爬虫框架（`async def start()`） |
| Redis | 全局去重 + 关键词进度 + 断点续爬 |
| PostgreSQL | `public.social_media` 表持久化存储 |
| curl_cffi | TLS 指纹伪装 |
| xhshow | 小红书接口签名生成 |

## 快速开始

### 环境准备

```bash
conda activate spider          # Python 3.12.0
pip install -r requirements.txt
```

### 配置

1. **Cookie**: 将小红书登录后的 Cookie 放入 `src/spiders/socialmedia/xhs/xhs_cookies.json`

2. **环境变量** (`.env`):

```env
REDIS_URL=redis://:password@localhost:6379/0
POSTGRES_URL=postgresql://user:pass@localhost/crawl_data
```

3. **爬取参数** (`src/spiders/socialmedia/xhs/xhs_config.py`):

```python
KEYWORD = ["美食", "旅行"]      # 搜索关键词
MAX_NOTES_COUNT = 20            # 每个关键词最大采集数
SORT_TYPE = "general"           # general | popularity_descending | time_descending
NOTE_TYPE = 0                   # 0=不限 1=视频 2=图文
```

### 启动

```bash
# 全量采集（默认）
scrapy crawl xiaohongshu

# 增量采集（每轮每个关键词采 incre_num 条新笔记）
scrapy crawl xiaohongshu -a mode=incremental -a incre_num=5

# 指定关键词 + 数量
scrapy crawl xiaohongshu -a keyword=美食 -a num=10
```

## 项目结构

```
XHSWebCrawler/
├── config/
│   ├── base.py                 # Scrapy settings 加载（YAML → 环境变量注入）
│   └── base.yaml               # 全局配置
├── src/
│   ├── spiders/socialmedia/xhs/
│   │   ├── xiaohongshu.py      # 主爬虫：搜索 → 详情 → 入库
│   │   ├── xhs_config.py       # 爬虫参数配置
│   │   ├── xhs_sign.py         # 接口签名
│   │   └── xhs_cookies.json    # Cookie 文件（已 gitignore）
│   ├── pipelines/
│   │   ├── postgres_pipeline.py # PostgreSQL 入库（ON CONFLICT 去重）
│   │   └── console_pipeline.py  # 控制台输出（已禁用）
│   ├── middlewares/
│   │   └── curl_cffi_handler.py # curl_cffi 下载中间件
│   └── deduplication/
│       ├── redis_helper.py     # Redis 去重 + 断点续爬
│       └── README.md           # 去重逻辑文档
├── requirements.txt
└── scrapy.cfg
```

## 工作原理

### 采集流程

1. **启动** — `start()` 遍历关键词列表，跳过 Redis 中标记 `done=1` 的关键词
2. **搜索** — 调用搜索 API 获取笔记列表，返回 `note_card` 原始数据
3. **去重** — 每篇笔记在 yield 请求前通过 Redis SET `SISMEMBER` 检查
4. **详情** — 获取笔记详情，解析标题、内容、互动数据等
5. **入库** — `PostgresPipeline` 写入 PostgreSQL，`ON CONFLICT DO NOTHING` 防重复
6. **计数** — `INCR` 计数器，达到目标数后标记关键词 `done`

### 数量控制

`_scheduled` 计数器在 **yield 请求之前** 递增，配合断点续爬时的 `remaining`（缺口数）作为调度上限，防止搜索结果页批量 yield 导致超采。

### Redis Key 结构

```
                        ┌─── 共享去重 ───┐
{xiaohongshu}:notes              SET    "url|search"            全局去重，全量/增量共用

{xiaohongshu}:kw:{keyword}       HASH   {target, done}          全量关键词状态
{xiaohongshu}:kw:{keyword}:cnt   STRING                          全量已采集计数

{xiaohongshu}:incr:kw:{keyword}  HASH   {target, done}          增量关键词状态
{xiaohongshu}:incr:kw:{keyword}:cnt STRING                       增量已采集计数
```

### 增量采集

增量模式以**轮**为推进单位，每轮每个关键词各采集 `incre_num` 条新笔记，必须全部 keyword 完成才推进到下一轮。

- **新关键词守卫**：增量启动时检测未跑过全量的新 keyword，warning + CloseSpider 退出
- **共享去重**：全量和增量共用 `{xhs}:notes` SET，天然互不重复
- **断点续爬**：中断后重跑自动补缺 undone 的 keyword，不动 target
- **轮级门控**：全部 keyword done=1 → `advance_round` → target += incre_num → 下一轮

```bash
scrapy crawl xiaohongshu -a mode=incremental -a incre_num=5
```

详见 `src/spiders/socialmedia/xhs/incremental-design.md`。

### 数据库表

表 `public.social_media` 以 `(platform, data_type, item_id)` 作为唯一约束，字段包括 `title`、`content`、`author`、`like_count`、`comment_count`、`share_count`、`raw_data` 等，支持多平台数据汇总。
