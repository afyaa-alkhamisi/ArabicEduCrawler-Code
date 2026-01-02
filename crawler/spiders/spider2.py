# crawler/spiders/arabic_wiki_spider.py
import json
from urllib.parse import unquote
import scrapy
from datetime import datetime
from scrapy import signals
from crawler.extractors.custom_extractors2 import CustomSite2Extractor
from crawler.utils.metadata import extract_metadata
from crawler.middlewares.config_middleware import ConfigMiddleware


class WikipediaSpider(scrapy.Spider):
    name = "arabic_wiki"
    allowed_domains = ["ar.wikipedia.org"]

    # Crawl limits
    max_depth = 5
    max_articles = 5000
    max_articles_per_page = 100
    page_limit = 1000

    # Counters
    total_articles = 0
    total_pages = 0
    start_time = None

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
            with open("arabic_wiki_crawl_stats.json", "w", encoding="utf-8") as f:
                json.dump(stats_log, f, ensure_ascii=False, indent=2)
            self.logger.info(
                f"📊 Crawled {self.total_pages} pages "
                f"(at {pages_per_min:.2f}/min), scraped {self.total_articles} items "
                f"(at {items_per_min:.2f}/min)"
            )
        else:
            self.logger.warning(
                "⚠️ No valid items scraped — skipping stats export.")

    async def start(self):
        """Entry point using site configuration file."""
        config_mw = ConfigMiddleware()
        self.site_config = config_mw.get_site_config("ar.wikipedia.org")
        start_urls = self.site_config.get("start_urls", [])
        use_js = self.site_config.get("use_js", False)

        for url in start_urls:
            self.logger.info(f"[Depth 0] Starting from category: {url}")
            yield scrapy.Request(
                url,
                callback=self.parse_category,
                meta={"config": self.site_config, "depth": 0,
                      "subcategory": "", "playwright": use_js},
            )

    def parse_category(self, response):
        if self.total_pages >= self.page_limit or self.total_articles >= self.max_articles:
            if not getattr(self, "_stop_logged", False):
                self.logger.warning(
                    "⚠️ Reached global limits — stopping crawl.")
                self._stop_logged = True
            return

        config = response.meta["config"]
        depth = response.meta.get("depth", 0)
        subcategory = response.meta.get("subcategory", "")

        self.total_pages += 1
        self.logger.info(
            f"[Depth {depth}] Crawling: {response.url} ({self.total_pages}/{self.page_limit})")

        article_links = response.xpath(
            config["xpaths"]["article_links"]).getall() or []
        subcategories = response.xpath(
            config["xpaths"]["subcategory_links"]).getall() or []

        # Crawl articles
        for href in article_links[: self.max_articles_per_page]:
            if self.total_articles >= self.max_articles:
                break
            if any(x in href for x in ["بوابة:", "index.php", "تصنيف:"]):
                continue
            full_url = response.urljoin(href)
            full_url_ar = unquote(full_url)  # <-- decode URL
            yield scrapy.Request(
                full_url_ar,
                callback=self.parse_article,
                meta={**response.meta, "subcategory": subcategory,
                      "depth": depth + 1},
            )

        # Recurse into subcategories
        if depth < self.max_depth:
            for sub_href in subcategories:
                sub_url_ar = unquote(response.urljoin(sub_href))  # <-- decode
                yield scrapy.Request(
                    sub_url_ar,
                    callback=self.parse_category,
                    meta={
                        **response.meta, "subcategory":  unquote(sub_href.split(":")[-1]), "depth": depth + 1},
                )

    def parse_article(self, response):
        config = response.meta["config"]
        subcategory = response.meta.get("subcategory", "")

        extractor = CustomSite2Extractor(response, config)
        item = extractor.extract()
        text = item.get("content", "")

        # Skip articles with empty or too short content
        if not text or len(text.strip()) < 50:
            self.logger.warning(
                f"⚠️ Skipping short or empty article: {response.url}")
            return

        # Extract metadata
        metadata = extract_metadata(
            response, xpaths=config.get("xpaths", {}), raw_content=text
        )
        self.total_articles += 1
        self.logger.info(
            f"✅ Scraped article #{self.total_articles}: {response.url}")

        item = {
            "url": unquote(response.url),  # decode article URL
            "title": item.get("title"),
            "content": text,
            "metadata": {
                "source": "Arabic Wikipedia",
                "author": item.get("author"),
                "subcategory": subcategory,
                "date": item.get("date"),
                "article_length": len(text),
                "crawl_meta": metadata,
            },
        }
        yield item
