from urllib.parse import urlparse
import scrapy
import datetime
import json
from crawler.extractors.custom_extractors1 import CustomSite1Extractor
from crawler.utils.metadata import extract_metadata
from scrapy import signals
from crawler.middlewares.config_middleware import ConfigMiddleware
from urllib.parse import unquote


class AlukahSpider(scrapy.Spider):
    name = "alukah"
    allowed_domains = ["alukah.net"]

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(AlukahSpider, cls).from_crawler(
            crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened,
                                signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed,
                                signal=signals.spider_closed)
        return spider

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.page_count_per_seed = {}  # pages per seed
        self.page_limit_per_seed = 500  # maximum pages per seed
        self.page_count = 0
        self.item_count = 0
        self.start_time = None
        self.stats_log = {}

    def spider_opened(self, spider):
        self.start_time = datetime.datetime.now()

    def spider_closed(self, spider, reason):
        end_time = datetime.datetime.now()
        duration_min = (end_time - self.start_time).total_seconds() / 60
        pages_per_min = self.page_count / duration_min if duration_min > 0 else 0
        items_per_min = self.item_count / duration_min if duration_min > 0 else 0

        self.stats_log = {
            "spider": self.name,
            "pages_crawled": self.page_count,
            "items_scraped": self.item_count,
            "pages_per_seed": self.page_count_per_seed,
            "pages_per_min": round(pages_per_min, 2),
            "items_per_min": round(items_per_min, 2),
            "duration_minutes": round(duration_min, 2),
            "reason": reason,
            "start_time": self.start_time.isoformat(),
            "finished": end_time.isoformat(),
        }

        with open("aluka_crawl_stats.json", "w", encoding="utf-8") as f:
            json.dump(self.stats_log, f, ensure_ascii=False, indent=2)

        self.logger.info(
            f"Crawled {self.page_count} pages (at {pages_per_min:.2f} pages/min), "
            f"scraped {self.item_count} items (at {items_per_min:.2f} items/min)"
        )

    def start_requests(self):

        config_mw = ConfigMiddleware()
        site_config = config_mw.get_site_config("alukah.net")
        start_urls = site_config.get("start_urls", [])

        for url in start_urls:
            seed_key = url.rstrip("/").split("/")[-2]  # e.g. "library"
            yield scrapy.Request(
                url=f"{url}page/1/",
                callback=self.parse,
                meta={
                    "site_config": site_config,
                    "seed_url": url,
                    "seed_key": seed_key,
                    "page_number": 1,
                },
            )

    def parse(self, response):
        site_config = response.meta["site_config"]
        seed_url = response.meta["seed_url"]
        seed_key = response.meta["seed_key"]
        page_number = response.meta["page_number"]
        # Increment page count
        self.page_count += 1
        self.page_count_per_seed[seed_key] = self.page_count_per_seed.get(
            seed_key, 0) + 1
        self.logger.info(f"[{seed_key}] Crawled page {page_number}")

        # Stop if limit reached
        if self.page_count_per_seed[seed_key] > self.page_limit_per_seed:
            self.logger.warning(
                f"🚫 Reached page limit ({self.page_limit_per_seed}) for {seed_key}. Stopping pagination."
            )
            return

        # ✅ Extract table rows directly in spider
        rows_xpath = site_config.get(
            "rows_xpath", '//*[@id="print_area"]/div[4]//tr')
        rows = response.xpath(rows_xpath)
        self.logger.info(f"Found {len(rows)} rows on {response.url}")

        for row in rows:
            title = row.xpath(site_config.get(
                "title_xpath", "./td[1]/a/text()")).get()
            relative_url = row.xpath(site_config.get(
                "url_xpath", "./td[1]/a/@href")).get()
            if not relative_url:
                continue

            full_url = response.urljoin(relative_url)
            full_url_arabic = unquote(full_url)  # decode percent-encoding

            author = row.xpath(site_config.get(
                "author_xpath", "./td[2]/text()")).get()
            date = row.xpath(site_config.get(
                "date_xpath", "./td[3]/text()")).get()
            views = row.xpath(site_config.get(
                "views_xpath", "./td[4]/text()")).get()

            yield scrapy.Request(
                url=full_url_arabic,
                callback=self.parse_article,
                meta={
                    "site_config": site_config,
                    "item_meta": {
                        "title": title.strip() if title else None,
                        "url": full_url_arabic,
                        "author": author.strip() if author else None,
                        "date": date.strip() if date else None,
                        "views": views.strip() if views else None,
                    },
                },
            )

        # Pagination — next page
        next_page_num = page_number + 1
        if self.page_count_per_seed[seed_key] < self.page_limit_per_seed:
            next_page = f"{seed_url}page/{next_page_num}/"
            yield scrapy.Request(
                url=next_page,
                callback=self.parse,
                meta={
                    "site_config": site_config,
                    "seed_url": seed_url,
                    "seed_key": seed_key,
                    "page_number": next_page_num,
                },
            )

    def parse_article(self, response):
        item_meta = response.meta.get("item_meta", {})
        site_config = response.meta.get("site_config", {})

        # ✅ Use CustomSite1Extractor only for article content
        extractor = CustomSite1Extractor(response, site_config)
        content = extractor.extract_article_content()

        item = {
            "url": item_meta.get("url"),
            "title": item_meta.get("title"),
            "content": content,
            "metadata": {
                "author": item_meta.get("author"),
                "date": item_meta.get("date"),
                "views": item_meta.get("views"),
                "crawl_meta": extract_metadata(response),
            },
        }
        self.item_count += 1
        yield item
