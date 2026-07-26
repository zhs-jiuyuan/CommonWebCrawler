import logging
import os
from typing import Optional

from cloakbrowser import launch

logger = logging.getLogger(__name__)

_log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(_log_dir, exist_ok=True)
_log_file = os.path.join(_log_dir, "scrapy.log")

if not any(isinstance(h, logging.FileHandler) and h.baseFilename == os.path.abspath(_log_file) for h in logger.handlers):
    _file_handler = logging.FileHandler(_log_file, encoding="utf-8")
    _file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(_file_handler)
    logger.setLevel(logging.DEBUG)

_DEFAULT_URL = "https://www.autohome.com.cn/chengdu/"
_DEFAULT_TIMEOUT = 30_000

_FIND_CAR_XPATH = '//*[@id="app"]/div[1]/div[2]/section[2]/div[1]/div[2]/div/div[1]/a'

_BLOCK_RESOURCE_TYPES = {"image", "ping", "media", "font"}


def _block_unnecessary(page):
    block_types = _BLOCK_RESOURCE_TYPES
    logger.info("Blocking resource types: %s", sorted(block_types))

    def handle(route):
        if route.request.resource_type in block_types:
            route.abort()
            return
        route.continue_()

    page.route("**/*", handle)


def _locate_button(page):
    strategies = [
        f'xpath={_FIND_CAR_XPATH}',
        'a:has-text("找 车")',
        'a.bg-gradient-to-r',
    ]
    for idx, selector in enumerate(strategies):
        loc = page.locator(selector)
        if loc.count() > 0:
            logger.info("Find-car button located via strategy %d: %s", idx + 1, selector)
            return loc.first
    raise RuntimeError("找不到'找车'按钮")


def _click_find_car(page, context, timeout):
    btn = _locate_button(page)
    logger.info("Clicking find-car button, waiting for new tab (timeout=%dms)", timeout)
    with context.expect_page(timeout=timeout) as event_info:
        btn.click()
    new_page = event_info.value
    logger.info("New tab opened: %s", new_page.url)
    new_page.wait_for_load_state('networkidle')
    logger.info("New tab fully loaded")


def get_cookies(
    url: Optional[str] = None,
    timeout: Optional[int] = None,
) -> dict[str, str]:
    url = url or _DEFAULT_URL
    timeout = timeout or _DEFAULT_TIMEOUT

    logger.info("Launching browser")
    browser = launch()
    try:
        context = browser.new_context()
        page = context.new_page()

        _block_unnecessary(page)

        logger.info("Navigating to %s", url)
        page.goto(url)
        page.wait_for_load_state('networkidle')
        logger.info("Page loaded")

        _click_find_car(page, context, timeout)

        cookies = context.cookies()
        logger.info("Extracted %d cookies", len(cookies))
        return {c["name"]: c["value"] for c in cookies}
    finally:
        browser.close()
        logger.info("Browser closed")


__all__ = ["get_cookies"]
