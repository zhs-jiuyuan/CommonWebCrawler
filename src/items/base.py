import scrapy
from datetime import datetime
from itemadapter import ItemAdapter


class BaseItem(scrapy.Item):
    spider_name = scrapy.Field()
    target_type = scrapy.Field()
    url = scrapy.Field()
    task_id = scrapy.Field()
    crawl_time = scrapy.Field()
    data = scrapy.Field()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "crawl_time" not in self or self.get("crawl_time") is None:
            self["crawl_time"] = datetime.now().isoformat()

    def validate(self):
        adapter = ItemAdapter(self)

        required_fields = ["url", "spider_name"]
        for field in required_fields:
            if not adapter.get(field):
                raise ValueError(f"Required field '{field}' is missing.")

        return True
