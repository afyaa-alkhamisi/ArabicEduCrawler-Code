import os

BOT_NAME = "crawler"

SPIDER_MODULES = ["crawler.spiders"]
NEWSPIDER_MODULE = "crawler.spiders"

# ----------------- Pipelines -----------------
ITEM_PIPELINES = {
    "crawler.pipelines.core_filter_pipeline.CoreFilterPipeline": 300,
    "crawler.pipelines.mongo_pipeline.MongoDBPipeline": 400,
}

# ----------------- Downloader Middlewares -----------------
DOWNLOADER_MIDDLEWARES = {
    "crawler.middlewares.config_middleware.ConfigMiddleware": 500,
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    "scrapy_user_agents.middlewares.RandomUserAgentMiddleware": 400,
}

# ----------------- Playwright Settings -----------------
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {"headless": True}
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 60 * 1000  # 60 seconds

# ----------------- MongoDB Pipeline Settings -----------------
MONGO_URI = os.getenv(
    "MONGO_URI", "mongodb://mongoadmin:mongoadmin@mongo:27017/")
MONGO_DB = "crawler_db"

# ----------------- AutoThrottle Settings -----------------
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 5
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
AUTOTHROTTLE_DEBUG = False

# ----------------- Politeness and Ethical Crawling -----------------
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 2.0
RANDOMIZE_DOWNLOAD_DELAY = True
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8
CONCURRENT_REQUESTS_PER_IP = 8

# ----------------- Retry and Timeout Settings -----------------
RETRY_ENABLED = True
RETRY_TIMES = 3
DOWNLOAD_TIMEOUT = 30

# ----------------- Logging -----------------
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"

# ----------------- HTTP Cache -----------------
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 86400
HTTPCACHE_DIR = "httpcache"

# ----------------- Extensions -----------------
EXTENSIONS = {
    "scrapy.extensions.logstats.LogStats": 50,
}

LOGSTATS_INTERVAL = 1800  # Log stats every 30 minutes (1800 seconds)
# ----------------------------------------------------------
