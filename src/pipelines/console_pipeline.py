import json
from datetime import datetime


class ConsolePipeline:

    def __init__(self):
        self.item_count = 0
        self.start_time = None

    def open_spider(self, spider):
        self.start_time = datetime.now()
        spider.logger.info("[ConsolePipeline] opened")

    def process_item(self, item, spider):
        self.item_count += 1
        data = dict(item)
        data.setdefault("_pipeline_ts", datetime.now().isoformat())

        spider.logger.info(
            "[ConsolePipeline] item #%d\n%s",
            self.item_count,
            json.dumps(data, ensure_ascii=False, indent=2, default=str),
        )
        return item

    def close_spider(self, spider):
        elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        spider.logger.info(
            "[ConsolePipeline] closed | total_items=%d elapsed=%.1fs",
            self.item_count, elapsed,
        )
