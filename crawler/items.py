import scrapy


class ArabicEduCrawlerItem(scrapy.Item):
    title = scrapy.Field()
    description = scrapy.Field()
