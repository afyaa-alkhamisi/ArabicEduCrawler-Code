# pipelines/core_filter_pipeline.py
from datetime import datetime
import datetime
import datetime
import json
import os
from scrapy.exceptions import DropItem
from crawler.utils.filters import is_arabic, normalize_arabic_text, get_md5_hash
from crawler.utils.metadata import extract_metadata
import datetime
from crawler.utils.filters import logger as ft_logger

FILTER_LOG_PATH = "filtered_items.jsonl"


class CoreFilterPipeline:
    """
    Pipeline that filters and cleans items:
    - Filters out short, duplicate, or non-Arabic items
    - Removes very short content (Content length check)
    - Deduplicates using MD5 hashes ((hash + normalization))
    - Removes non-Arabic text (Arabic content check)
    - Logs all dropped items to a JSONL file
    """

    def __init__(self, normalize_func=None, min_length=10, arabic_check=True):
        self.seen_hashes = set()
        self.normalize_func = normalize_func or normalize_arabic_text
        self.min_length = min_length
        self.arabic_check = arabic_check

        if not os.path.exists(FILTER_LOG_PATH):
            open(FILTER_LOG_PATH, "w", encoding="utf-8").close()

    @classmethod
    def from_crawler(cls, crawler):
        normalize_func = getattr(
            crawler.settings, "DEDUP_NORMALIZE_FUNC", None)
        min_length = crawler.settings.getint("MIN_CONTENT_LENGTH", 10)
        arabic_check = crawler.settings.getbool("ARABIC_CHECK_ENABLED", True)
        return cls(
            normalize_func=normalize_func,
            min_length=min_length,
            arabic_check=arabic_check,
        )

    def process_item(self, item, spider):
        timestamp = datetime.datetime.utcnow().isoformat()
        url = item.get("url", "").strip()
        # Collect all possible content fields
        content = (
            item.get("full_poem")
            or item.get("article")
            or item.get("content")
            or ""
        )
        normalized = self.normalize_func(content)
        # Compute accurate UTF-8 byte length
        content_length = len(normalized.encode("utf-8"))

        # Update item
        item["content_length"] = content_length

        # --- Compute single, universal hash ---
        content_hash = get_md5_hash(f"{url}_{normalized}")
        item["content_hash_md5"] = content_hash

        # --- Deduplication ---
        if content_hash in self.seen_hashes:
            spider.logger.warning(f"Dropped duplicate: {url}")
            self._log(url, content, "duplicate_content", timestamp)
            raise DropItem("Duplicate content")
        self.seen_hashes.add(content_hash)

        # --- Minimum length check ---
        if content_length < self.min_length:
            spider.logger.warning(
                f"Dropped: content too short ({len(normalized)}) | {item.get('url', '')}"
            )

            spider.logger.warning(
                f"Dropped: content too short ({content_length}) | {item.get('url')}"
            )
            self._log(url, content, "too_short", timestamp)
            raise DropItem("Content too short")

        # --- Arabic content check (optional) ---
        if self.arabic_check:
            arabic_result = is_arabic(normalized)
            if not arabic_result["is_arabic"]:
                ft_logger.info(
                    f"Non-Arabic detected: {url} | reason: {arabic_result.get('reason')} | labels={arabic_result.get('labels')} "
                    f"| confs={arabic_result.get('confidences')}"
                )
                self._log(
                    url,
                    content,
                    f"Non-Arabic detected:  {arabic_result.get('reason', '')}",
                    timestamp,
                    labels=arabic_result.get("labels", []),
                    confidences=arabic_result.get("confidences", []),
                )
                raise DropItem("Non-Arabic content")
            item["lang_labels"] = arabic_result["labels"]
            item["lang_confidences"] = arabic_result["confidences"]

        return item

    def _log(self, url, text, reason, timestamp, labels=None, confidences=None):
        entry = {
            "timestamp": timestamp,
            "url": url,
            "reason": reason,
            "labels": labels or [],
            "confidences": confidences or [],
            "sample_text": text[:100],
        }
        with open(FILTER_LOG_PATH, "a", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False)
            f.write("\n")
