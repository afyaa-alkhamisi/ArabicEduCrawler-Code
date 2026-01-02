# crawler/spiders/adab_ajax_spider.py
import scrapy
from scrapy.selector import Selector
from scrapy import signals
import json
from datetime import datetime
from crawler.utils.metadata import extract_metadata
from crawler.extractors.custom_extractors3 import CustomSite3Extractor
from scrapy_playwright.page import PageMethod
from crawler.middlewares.config_middleware import ConfigMiddleware


class AdabSpider(scrapy.Spider):
    """
    Spider to scrape literary posts and poems from adab.com via AJAX.
    Supports site_config from middleware and uses Playwright for detail pages.
    """

    name = "adab"
    allowed_domains = ["adab.com"]
    base_url = "https://adab.com/post/search_get_post"

    custom_settings = {
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 60 * 1000,
        "ROBOTSTXT_OBEY": False,
    }

    max_pages = 3000  # maximum AJAX pages to crawl
    total_pages = 0
    total_items = 0
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
        self.logger.info("🚀 Started AdabAjaxSpider at %s", self.start_time)

    def spider_closed(self, spider, reason):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds() / 60  # minutes
        pages_per_min = self.total_pages / duration if duration > 0 else 0
        items_per_min = self.total_items / duration if duration > 0 else 0

        stats = {
            "spider": self.name,
            "pages_crawled": self.total_pages,
            "items_scraped": self.total_items,
            "pages_per_min": round(pages_per_min, 2),
            "items_per_min": round(items_per_min, 2),
            "duration_minutes": round(duration, 2),
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "reason": reason,
        }

        with open("adab_crawl_stats.json", "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        self.logger.info(
            f"📊 Finished crawling — Pages: {self.total_pages}, Items: {self.total_items}, "
            f"Speed: {pages_per_min:.2f} pages/min, {items_per_min:.2f} items/min."
        )

    def start_requests(self):
        config_mw = ConfigMiddleware()
        site_config = config_mw.get_site_config("adab.com")
        for page in range(1, self.max_pages + 1):
            form_data = {
                "page": str(page),
                "seg3": "key",
                "seg4": "",
                "genre_filter_list": "",
                "writing_type_filter_list": "",
                "tags_select": "",
                "search_key": "",
                "user_type": "",
                "era_select": "",
                "country": "-1",
                "gender": "",
                "selected_country": "",
                "sort_by": "",
            }

            yield scrapy.FormRequest(
                url=self.base_url,
                formdata=form_data,
                method="POST",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "Origin": "https://adab.com",
                    "Referer": "https://adab.com/",
                },
                callback=self.parse,
                meta={"page": page},
            )

    def parse(self, response):
        """Parse AJAX response and extract poem listings."""
        page = response.meta["page"]
        site_config = response.meta.get("site_config", {})

        self.total_pages += 1

        # Try JSON first
        html_fragment = ""
        try:
            json_data = json.loads(response.text)
            html_fragment = json_data.get("html") or json_data.get(
                "view") or json_data.get("data") or ""
        except json.JSONDecodeError:
            # fallback: treat response as raw HTML
            html_fragment = response.text
            self.logger.warning(
                f"⚠️ Page {page} returned non-JSON, using raw HTML.")

        if not html_fragment:
            self.logger.warning(f"⚠️ No content returned for page {page}")
            return

        html_string = "".join(html_fragment) if isinstance(
            html_fragment, list) else html_fragment
        html_selector = Selector(text=html_string)

        extractor = CustomSite3Extractor(
            response, site_config, selector=html_selector)
        posts = extractor.extract_rows()
        self.logger.info(f"📄 Page {page}: Found {len(posts)} posts")

        for post_info in posts:
            poem_metadata = {
                "author": post_info.get("author", "").strip(),
                "profile_url": post_info.get("profile_url", "").strip(),
                "post_date": post_info.get("post_date", "").strip(),
                "page": str(post_info.get("page", page)).strip(),
                "excerpt": post_info.get("excerpt", "").strip(),
            }

            poem_url = post_info.get("link")
            if poem_url:
                yield response.follow(
                    url=poem_url,
                    callback=self.parse_poem,
                    meta={
                        "poem_metadata": poem_metadata,
                        "poem_url": poem_url,
                        "site_config": site_config,
                        "playwright": True,
                        "playwright_page_methods": [
                            PageMethod("wait_for_selector",
                                       "#post_content_view", timeout=60000)
                        ],
                        "playwright_page_goto_kwargs": {"timeout": 120000, "wait_until": "domcontentloaded"},
                    },
                )
            else:
                self.total_items += 1
                yield {
                    "title": post_info.get("title", "").strip(),
                    "poem_metadata": poem_metadata,
                    "url": post_info.get("link", "").strip(),
                    "source": "adab.com",
                }

    def parse_poem(self, response):
        """Extract full poem content using CustomSite3Extractor."""
        poem_metadata = response.meta["poem_metadata"]
        site_config = response.meta.get("site_config", {})

        extractor = CustomSite3Extractor(response, site_config)
        full_poem = extractor.extract_article()
        poem_length = len(full_poem.encode("utf-8"))

        if poem_length == 0:
            self.logger.warning(f"Dropped: empty poem | {response.url}")
            return

        self.total_items += 1
        item = {
            "url": response.meta.get("poem_url", ""),
            "title": response.xpath("//h2/text()").get(default="").strip(),
            "full_poem": full_poem or "",
            "metadata": {
                "source": "Adab",
                "author": poem_metadata.get("author"),
                "profile_url": poem_metadata.get("profile_url"),
                "post_date": response.meta.get("poem_metadata", {}).get("post_date"),
                "page": response.meta.get("poem_metadata", {}).get("page"),
                "excerpt": response.meta.get("poem_metadata", {}).get("excerpt"),
                "poem_length": poem_length,
                "crawl_meta": extract_metadata(response),
            },
        }
        yield item
