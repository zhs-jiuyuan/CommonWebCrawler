from src.spiders.base import BaseSpider


class XiaohongshuSpider(BaseSpider):
    name = "xiaohongshu"
    allowed_domains = ["xiaohongshu.com"]
    start_urls = ["https://www.xiaohongshu.com"]

    def parse(self, response):
        pass
