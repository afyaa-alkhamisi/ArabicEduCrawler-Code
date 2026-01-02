# crawler/extractors/custom_extractors2.py
import re


class CustomSite2Extractor:
    def __init__(self, response, config):
        self.response = response
        self.config = config

    def extract(self):
        xpaths = self.config.get("xpaths", {})

        # Extract title
        title = "".join(self.response.xpath(
            xpaths.get("title", "")).getall()).strip() or None

        # Extract last edited date
        lastmod_text = self.response.xpath(
            xpaths.get("date", "")
        ).get(default="").strip()
        match = re.search(r'(\d{1,2} \S+ \d{4})', lastmod_text)
        last_edited = match.group(1) if match else None

        # Extract article paragraphs and join as single string
        paragraphs = self.response.xpath(
            xpaths.get("article_paragraphs", "")
        ).getall()
        article = " ".join([p.strip() for p in paragraphs if p.strip()])
        article = re.sub(r'\s+', ' ', article)  # normalize whitespace

        return {
            "title": title,
            "date": last_edited,
            "content": article or None,  # ensure key matches pipeline expectation
        }
