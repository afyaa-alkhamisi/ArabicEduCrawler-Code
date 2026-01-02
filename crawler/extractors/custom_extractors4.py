# crawler/extractors/custom_extractor_shamela.py
import re


class CustomSite4Extractor:
    """
    Extracts structured book metadata from Shamela-like pages.
    """

    def __init__(self, response):
        self.response = response

    def extract_book_metadata(self):
        """
        Extracts metadata from <div class="nass"> description block.
        Returns dict: title, author, publisher, edition, pages
        """
        desc_block = self.response.css("div.nass").xpath("string()").get()
        metadata = {
            "title": None,
            "author": None,
            "publisher": None,
            "edition": None,
            "pages": None,
        }

        if not desc_block:
            return metadata

        text = desc_block.replace("\xa0", " ").replace(
            "\r", "").replace("\n", "\n")
        text = re.sub(r"[\[\]]", "", text)
        text = re.sub(r"\s{2,}", " ", text)

        patterns = {
            "title": r"الكتاب[:：]\s*(.+?)(?=\n|المؤلف|الناشر|الطبعة|عدد الصفحات|صفحة المؤلف|$)",
            "author": r"المؤلف[:：]\s*(.+?)(?=\n|الناشر|الطبعة|عدد الصفحات|صفحة المؤلف|$)",
            "publisher": r"الناشر[:：]\s*(.+?)(?=\n|الطبعة|عدد الصفحات|صفحة المؤلف|$)",
            "edition": r"الطبعة[:：]?\s*(.+?)(?=\n|عدد الصفحات|صفحة المؤلف|$)",
            "pages": r"عدد الصفحات[:：]?\s*(\d+)",
        }

        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.DOTALL)
            if match:
                value = match.group(1).strip()
                # Remove surrounding brackets if any
                value = re.sub(r"^\[|\]$", "", value)
                if field == "pages":
                    try:
                        metadata[field] = int(value)
                    except ValueError:
                        metadata[field] = None  # fallback
                else:
                    metadata[field] = value

        return metadata
