from scrapy.selector import Selector


class CustomSite3Extractor:
    """
    Generalized extractor for both normal HTML sites and JSON+JS sites.

    Features:
    - Uses site_config for all XPaths
    - Can work on a full response or a Selector for HTML fragments
    - Supports row-based extraction (listing pages) and single article extraction
    - Strips all text and handles missing fields gracefully
    """

    def __init__(self, response, config, selector=None):
        """
        :param response: Scrapy response object (Playwright-rendered if needed)
        :param config: Site config dictionary with XPaths
        :param selector: Optional Selector for HTML fragments (e.g., from AJAX JSON)
        """
        self.response = response
        self.config = config or {}
        self.selector = selector or response

    # -------------------------
    # Listing page / rows
    # -------------------------
    def extract_rows(self):
        """Extract all posts on a listing page using rows_xpath."""
        rows_xpath = self.config.get("rows_xpath")
        if not rows_xpath:
            return []

        posts = self.selector.xpath(rows_xpath)
        results = []

        for post in posts:
            results.append({
                "title": self._extract(post, "title_xpath"),
                "excerpt": self._extract(post, "excerpt_xpath"),
                "author": self._extract(post, "author_xpath"),
                "profile_url": self._extract(post, "profile_url_xpath"),
                "post_date": self._extract(post, "date_xpath"),
                "link": self._extract(post, "url_xpath"),
            })
        return results

    # -------------------------
    # Article / full content
    # -------------------------
    def extract_article(self):
        """Extract full article or poem text from response or selector."""
        article_xpath = self.config.get("article_xpath")
        if not article_xpath:
            return ""

        parts = self.response.xpath(article_xpath).getall()
        if not parts and hasattr(self, 'selector') and self.selector != self.response:
            # fallback: try selector if response has no content
            parts = self.selector.xpath(article_xpath).getall()

        return "\n".join([line.strip() for line in parts if line.strip()])

    # -------------------------
    # Helper for individual fields
    # -------------------------
    def _extract(self, node, xpath_key):
        """Extract text or attribute from a node safely using config."""
        xpath = self.config.get(xpath_key)
        if not xpath:
            return ""
        try:
            value = node.xpath(xpath).get(default="") or ""
            return value.strip()
        except Exception as e:
            self.response.logger.debug(f"Extractor error for {xpath_key}: {e}")
            return ""
