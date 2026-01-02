import json
import re
import scrapy
from scrapy import signals
from scrapy_playwright.page import PageMethod
from datetime import datetime
from crawler.middlewares.config_middleware import ConfigMiddleware
from crawler.utils.metadata import extract_metadata
from crawler.extractors.custom_extractors4 import CustomSite4Extractor


class ShamelaSpider(scrapy.Spider):
    name = "shamela"
    allowed_domains = ["shamela.ws"]

    custom_settings = {
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 60 * 1000,
        "ROBOTSTXT_OBEY": True,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = None
        self.total_pages = 0
        self.total_articles = 0
        self.site_config = {}

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened,
                                signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed,
                                signal=signals.spider_closed)
        return spider

    def spider_opened(self, spider):
        self.start_time = datetime.now()
        self.logger.info(f"🕷️ Spider {self.name} started at {self.start_time}")

    def spider_closed(self, spider, reason):
        end_time = datetime.now()
        duration_min = (end_time - self.start_time).total_seconds() / 60
        pages_per_min = self.total_pages / duration_min if duration_min > 0 else 0
        items_per_min = self.total_articles / duration_min if duration_min > 0 else 0

        stats_log = {
            "spider": self.name,
            "pages_crawled": self.total_pages,
            "items_scraped": self.total_articles,
            "pages_per_min": round(pages_per_min, 2),
            "items_per_min": round(items_per_min, 2),
            "duration_minutes": round(duration_min, 2),
            "reason": reason,
            "start_time": self.start_time.isoformat(),
            "finished": end_time.isoformat(),
        }

        if self.total_articles > 0:
            with open(f"{self.name}_crawl_stats.json", "w", encoding="utf-8") as f:
                json.dump(stats_log, f, ensure_ascii=False, indent=2)
            self.logger.info(
                f"📊 Crawled {self.total_pages} pages (at {pages_per_min:.2f}/min), "
                f"scraped {self.total_articles} items (at {items_per_min:.2f}/min)"
            )
        else:
            self.logger.warning(
                "⚠️ No valid items scraped — skipping stats export.")

    # ----------------- Main Crawl -----------------
    def start_requests(self):
        config_mw = ConfigMiddleware()
        self.site_config = config_mw.get_site_config("shamela.ws")

        start_urls = self.site_config.get("start_urls", [])
        for url in start_urls:
            yield scrapy.Request(
                url=url,
                meta={"playwright": True, "site_config": self.site_config},
                callback=self.parse_categories,
            )
    # ----------------- Parsing Methods -----------------

    def parse_categories(self, response):
        config = response.meta.get("site_config", {})
        # Extract up to 5 category links
        category_links = response.xpath(
            config.get("category_xpath", "")).getall()[:40]
        for link in category_links:
            yield scrapy.Request(
                url=response.urljoin(link),
                meta={"playwright": True, "site_config": config},
                callback=self.parse_category,
            )

    def parse_category(self, response):
        config = response.meta.get("site_config", {})
        book_links = response.xpath(
            config.get("book_xpath", "")).getall()[:100]
        for link in book_links:
            yield scrapy.Request(
                url=response.urljoin(link),
                meta={"playwright": True, "site_config": config},
                callback=self.parse_book,
            )
    # ----------------- Book and Article Parsing -----------------

    def parse_book(self, response):
        config = response.meta.get("site_config", {})

        # Extract book metadata using the custom extractor
        extractor = CustomSite4Extractor(response)
        book_metadata = extractor.extract_book_metadata()

        article_links = response.xpath(
            config.get("article_links_xpath", "")).getall()
        for link in article_links:
            if not link.strip() or link.startswith("javascript:"):
                continue

            match = re.search(r"/book/(\d+)/(\d+)", link)
            if match:
                book_id, page_number = map(int, match.groups())
                yield scrapy.Request(
                    url=response.urljoin(link),
                    meta={
                        "playwright": True,
                        "site_config": config,
                        "playwright_page_methods": [
                            PageMethod("wait_for_selector", "div.nass")
                        ],
                    },
                    callback=self.parse_article,
                    cb_kwargs={
                        "book_id": book_id,
                        "book_metadata": book_metadata,
                        "page_number": page_number,
                    },
                )
    # ----------------- Article Parsing -----------------

    def parse_article(self, response, book_id, book_metadata, page_number):
        config = response.meta.get("site_config", {})
        text_parts = response.xpath(
            config.get("content_xpath",
                       "//div[contains(@class,'nass')]//text()")
        ).getall()
        text = " ".join(t.strip() for t in text_parts if t.strip())
        text = re.sub(r"\s+", " ", text)

        if not text:
            self.logger.warning(f"Skipping empty article: {response.url}")
            return

        self.total_pages += 1
        self.total_articles += 1

        meta_info = extract_metadata(response, config, raw_content=text)
        item = {
            "url": response.url,
            "title": book_metadata.get("title"),
            "content": text,
            "metadata": {
                "source": "Shamela Library",
                "author": book_metadata.get("author"),
                "publisher": book_metadata.get("publisher"),
                "edition": book_metadata.get("edition"),
                "pages": book_metadata.get("pages"),
                "book_id": book_id,
                "page_number": page_number,
                "crawl_meta": meta_info,
            },
        }
        yield item
# ----------------- End of Spider -----------------
