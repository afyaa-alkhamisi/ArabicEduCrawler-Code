# crawler/extractors/custom_extractors.py
#
class CustomSite1Extractor:

    """
    Extract table rows and article content for alukah.net
    """

    def __init__(self, response, site_config):
        self.response = response
        self.site_config = site_config or {}

    def extract_rows(self):
        rows_xpath = self.site_config.get("rows_xpath")
        if not rows_xpath:
            print("No rows_xpath found in site_config!")
            return []
        rows = self.response.xpath(rows_xpath)
        print(f"Found {len(rows)} rows on {self.response.url}")
        return rows

    def extract_article(self, row):
        """
        Extract article info from a row element
        """
        x = self.site_config
        item = {}
        item["title"] = row.xpath(
            x.get("title_xpath", "./td[1]/a/text()")).get(default="").strip()
        relative_url = row.xpath(x.get("url_xpath", "./td[1]/a/@href")).get()
        item["url"] = self.response.urljoin(
            relative_url) if relative_url else None
        item["author"] = row.xpath(
            x.get("author_xpath", "./td[2]/text()")).get(default="").strip()
        item["date"] = row.xpath(
            x.get("date_xpath", "./td[3]/text()")).get(default="").strip()
        item["views"] = row.xpath(
            x.get("views_xpath", "./td[4]/text()")).get(default="").strip()
        return item

    def extract_article_content(self):
        """
        Extract full article content from article page
        """
        x = self.site_config
        paragraphs = self.response.xpath(
            x.get("article_xpath", "//div[@id='ArticleContent']//p//text()")).getall()
        content = " ".join([p.strip() for p in paragraphs if p.strip()])
        return content
