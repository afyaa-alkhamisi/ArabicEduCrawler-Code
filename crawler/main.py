from datetime import datetime
import time
import logging
import json
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy import signals
from crawler.spiders import spider1, spider2, spider3, spider4

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Store stats for all spiders
all_stats = []


def collect_spider_stats(spider):
    """Collect stats from spider after it closes"""
    stats = spider.crawler.stats.get_stats()
    all_stats.append({"spider": spider.name, "stats": stats})
    logger.info(f"Collected stats for {spider.name}")


def make_serializable(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def run_all():
    start_time = datetime.now()  # datetime object
    logger.info("🚀 Starting all spiders...")

    process = CrawlerProcess(get_project_settings())
    spiders = [
        spider1.AlukahSpider,
        spider2.WikipediaSpider,
        spider3.AdabSpider,
        spider4.ShamelaSpider,
    ]

    for spider_cls in spiders:
        crawler = process.create_crawler(spider_cls)
        # After spider closes, collect stats
        crawler.signals.connect(collect_spider_stats,
                                signal=signals.spider_closed)
        process.crawl(crawler)

    process.start()  # blocks until all spiders finish

    # duration in seconds
    elapsed = (datetime.now() - start_time).total_seconds()

    logger.info(
        f"✅ All spiders finished. Total time: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")

    logger.info(f"Collected stats for all spiders: {all_stats}")

    # Save aggregated stats to JSON
    with open("crawl_summary.json", "w", encoding="utf-8") as f:
        json.dump(all_stats, f, ensure_ascii=False,
                  indent=2, default=make_serializable)

    logger.info("📊 Aggregated stats saved to crawl_summary.json")


if __name__ == "__main__":
    run_all()
