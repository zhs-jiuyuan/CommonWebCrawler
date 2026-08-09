# CommonWebCrawler

通用多平台数据采集框架，基于 Scrapy 2.16。统一的数据采集流程：伪装 TLS 指纹请求 → 解析 API 数据 → Redis 全局去重 → 写入 PostgreSQL。新增平台只需继承对应分类基类即可接入。

## 能做什么

| 类别 | 平台 | 采集内容 | 状态 |
|------|------|----------|------|
| 社交媒体 | 小红书 | 笔记搜索 / 详情（全量、增量、关键词模式） | 完成 |
| 汽车 | 汽车之家 | 车型参数数据 | 进行中 |
| 游戏 | 游戏王大师决斗 | 卡牌数据与图片 | 骨架阶段 |
| 财经新闻 | 财联社 | — | 规划中 |

## 怎么做的

1. **请求** — `curl_cffi` 下载中间件伪装 Chrome/Safari TLS 指纹，规避反爬检测；小红书使用 `xhshow` 纯算法生成 x-s/x-t 签名，无需浏览器
2. **解析** — 各平台爬虫独立管理 Cookie、签名与解析逻辑，统一输出标准 Item
3. **去重** — Redis SET 全局 URL 去重，同时实现断点续爬与关键词进度追踪
4. **入库** — PostgreSQL 统一存储，`ON CONFLICT DO NOTHING` 防重复，多平台数据汇总至同一张表

爬虫类层次：`Scrapy.Spider` → `BaseSpider`（Item 创建、校验、统计）→ 各分类基类（社交/汽车/游戏/财经）→ 平台爬虫。

## 快速开始

```bash
conda activate spider
pip install -r requirements.txt
```

复制 `.env.example` 为 `.env`，配置 PostgreSQL 与 Redis 连接（各平台登录 Cookie 放入对应爬虫目录），即可启动：

```bash
scrapy crawl xiaohongshu -a keyword=美食 -a num=10   # 小红书
scrapy crawl autohome                                # 汽车之家
scrapy crawl masterduel                              # 游戏王大师决斗
```

并发数、延迟、限速、重试等全局参数集中在 `config/base.yaml` 管理，支持 `${VAR:default}` 环境变量注入。平台细节见各爬虫目录下的 README。
