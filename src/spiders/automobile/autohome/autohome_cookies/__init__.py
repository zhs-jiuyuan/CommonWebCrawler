from typing import Optional

from cloakbrowser import launch

_DEFAULT_URL = "https://www.autohome.com.cn/chengdu/"
_DEFAULT_TIMEOUT = 30_000

_FIND_CAR_XPATH = '//*[@id="app"]/div[1]/div[2]/section[2]/div[1]/div[2]/div/div[1]/a'


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
