from typing import Optional

from cloakbrowser import launch

_DEFAULT_URL = "https://www.autohome.com.cn/chengdu/"
_DEFAULT_TIMEOUT = 30_000

_FIND_CAR_XPATH = '//*[@id="app"]/div[1]/div[2]/section[2]/div[1]/div[2]/div/div[1]/a'

_BLOCK_RESOURCE_TYPES = {"image", "ping", "media", "font"}


def _block_unnecessary(page):
    block_types = _BLOCK_RESOURCE_TYPES

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
    for selector in strategies:
        loc = page.locator(selector)
        if loc.count() > 0:
            return loc.first
    raise RuntimeError("找不到'找车'按钮")


def _click_find_car(page, context, timeout):
    btn = _locate_button(page)
    with context.expect_page(timeout=timeout) as event_info:
        btn.click()
    new_page = event_info.value
    new_page.wait_for_load_state('networkidle')


def get_cookies(
    url: Optional[str] = None,
    timeout: Optional[int] = None,
) -> dict[str, str]:
    url = url or _DEFAULT_URL
    timeout = timeout or _DEFAULT_TIMEOUT

    browser = launch(headless=False)
    try:
        context = browser.new_context()
        page = context.new_page()

        _block_unnecessary(page)

        page.goto(url)
        page.wait_for_load_state('networkidle')

        _click_find_car(page, context, timeout)

        cookies = context.cookies()
        return {c["name"]: c["value"] for c in cookies}
    finally:
        browser.close()


__all__ = ["get_cookies"]
