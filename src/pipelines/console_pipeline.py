import json
from datetime import datetime


class ConsolePipeline:

    def process_item(self, item, spider):
        data = dict(item)
        data.setdefault("_pipeline_ts", datetime.now().isoformat())

        spider.logger.info(
            "[ConsolePipeline] item received:\n"
            f"  spider: {data.get('spider_name', '?')}\n"
            f"  url:    {data.get('url', '?')}\n"
            f"  keys:   {list(data.keys())}\n"
            f"  data:\n{json.dumps(data, ensure_ascii=False, indent=2, default=str)}"
        )
        return item
