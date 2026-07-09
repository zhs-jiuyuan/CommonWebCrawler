import scrapy
import time

from datetime import datetime
from src.items.base import BaseItem


class BaseSpider(scrapy.Spider):
    target_type = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = getattr(self, "mode", "incremental")
        self.date = getattr(self, "date", datetime.now().strftime("%Y-%m-%d"))
        self.task_id = getattr(self, "task_id", f"{self.name}_{self.date}_{int(time.time())}")

    def create_item(self, **kwargs) -> BaseItem:
        item = BaseItem()

        for key, value in kwargs.items():
            if key not in item.fields:
                item.fields[key] = scrapy.Field()

            item[key] = value

        item["spider_name"] = self.name

        if getattr(self, "target_type", None):
            item["target_type"] = self.target_type

        if getattr(self, "task_id", None):
            item["task_id"] = self.task_id

        try:
            item.validate()
        except Exception as e:
            # TODO: 后续增加 log 打印异常信息
            raise

        return item
    
    def closed(self, reason):
        stats = self.crawler.stats
