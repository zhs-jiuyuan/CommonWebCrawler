# autohome_cookies 重写设计规格

> 日期: 2026-07-26
> 状态: 已批准

## 背景

`autohome_cookies` 包当前存在但尚未被任何 spider 使用。原实现基于本地 AES-GCM 加密 + HTTP 截获生成 Cookie。由于汽车之家反爬升级，原方案不再适用，改为通过 CloakBrowser 打开浏览器实例模拟人工操作来获取 Cookie。

## 目标

重写 `autohome_cookies` 包，对外提供一个简洁的函数式 API，使用者只需一句调用即可获取汽车之家全站有效 Cookie。

## 技术选型

| 组件 | 用途 |
|------|------|
| CloakBrowser 0.4.8 | 启动反检测 Chromium 实例（Playwright 兼容 API） |
| Playwright API | 页面操作、元素定位、Cookie 提取 |

CloakBrowser 描述为 "Drop-in Playwright replacement"，其 API 与 Playwright 一致：

```python
from cloakbrowser import launch

browser = launch()
page = browser.new_page()
page.goto("...")
context.cookies()  # 获取所有 cookie
browser.close()
```

## API 设计

### 文件结构

```
autohome_cookies/
└── __init__.py    # 全部逻辑，对外暴露 get_cookies()
```

### 公开接口

```python
def get_cookies(
    url: str | None = None,
    timeout: int | None = None,
) -> dict[str, str]:
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `url` | `str \| None` | `"https://www.autohome.com.cn/chengdu/"` | 起始页面 URL |
| `timeout` | `int \| None` | `30000` | 等待新 Tab 的超时时间（毫秒） |

**返回值**：`dict[str, str]`，浏览器上下文内所有 Cookie 的 `{name: value}` 字典。

### 使用示例

```python
from autohome_cookies import get_cookies

cookies = get_cookies()
# => {"sessionid": "...", "autoid": "...", "__ah_uuid_ng": "..."}
```

## 内部执行流程

```
get_cookies()
│
├─ launch()                          # 启动 CloakBrowser 实例
├─ page.goto(url)                    # 1. 打开首页
├─ page.wait_for_load_state()        #    等待页面加载完成
├─ _click_find_car(page)             # 2. 点击"找车"按钮
├─ new_page = _wait_new_tab(ctx, t)  # 3. 等待新 Tab 出现
├─ cookies = context.cookies()       # 4. 提取全部 Cookie
├─ browser.close()                   #    关闭浏览器
└─ return {c["name"]: c["value"]}
```

### 核心辅助函数

#### `_click_find_car(page)` — 三重定位策略

按优先级尝试，任一命中即点击：

1. **XPath 精确匹配**
   ```
   //*[@id="app"]/div[1]/div[2]/section[2]/div[1]/div[2]/div/div[1]/a
   ```

2. **文本 + 标签匹配**
   ```
   page.locator("a:has-text('找 车')")
   ```

3. **Class 特征兜底**
   ```
   page.locator("a.bg-gradient-to-r")
   ```

全部失败则 `raise RuntimeError("找不到'找车'按钮")`。

#### `_wait_new_tab(context, timeout)` — 新 Tab 监听

监听 `context.on("page", handler)` 事件，在 timeout 毫秒内等待并返回新打开的 Page 对象。超时则 `raise TimeoutError("等待新Tab超时")`。

## 异常处理

| 场景 | 异常 |
|------|------|
| 按钮未找到 | `RuntimeError` |
| 新 Tab 超时未打开 | `TimeoutError` |
| 浏览器启动失败 | CloakBrowser 原始异常上抛 |
| 页面加载失败 | Playwright 原始异常上抛 |

所有异常不做静默处理，透明上抛给调用方。

## Cookie 共享说明

同一浏览器上下文（BrowserContext）中，相同域名下的 Cookie 是跨 Tab 共享的。因此虽然从新 Tab 中提取 Cookie，实际包含了从首页到新 Tab 整个会话期间积累的所有 Cookie。

## 依赖

```
cloakbrowser>=0.4.8
```

已在 ShareCreators 环境中安装。CloakBrowser 自带了 Playwright 依赖。
