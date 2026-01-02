import os
import uuid
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import logging


class MongoDBPipeline:
    """
    Pipeline to store crawled data into MongoDB:
    - raw_content: full text and crawl info
    - doc_metadata: metadata and enrichment info
    """

    def __init__(self, mongo_uri=None, db_name=None):
        # Reduce MongoDB debug noise
        logging.getLogger("pymongo").setLevel(logging.WARNING)
        # Load environment variables
        load_dotenv()

        mongo_user = os.getenv("MONGO_USER", "mongoadmin")
        mongo_pass = os.getenv("MONGO_PASSWORD", "mongoadmin")
        mongo_host = os.getenv("MONGO_CONTAINER", "mongo")
        mongo_port = os.getenv("MONGO_PORT", "27017")
        mongo_db = os.getenv("MONGO_DB", "crawlDB")

        # Allow override via Scrapy settings
        self.mongo_uri = mongo_uri or f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:{mongo_port}/{mongo_db}?authSource=admin"

        self.db_name = db_name or mongo_db

        # Connect with tuned heartbeat & timeout
        self.client = MongoClient(
            self.mongo_uri,
            serverSelectionTimeoutMS=5000,  # 5 sec timeout
            heartbeatFrequencyMS=10000  # default 10 sec between heartbeats
        )
        self.db = self.client[self.db_name]

        # Collections
        self.raw_collection = self.db["raw_content"]
        self.meta_collection = self.db["doc_metadata"]

    @classmethod
    def from_crawler(cls, crawler):
        """
        Scrapy entry point — reads settings if defined in settings.py
        """
        mongo_uri = crawler.settings.get("MONGO_URI", os.getenv("MONGO_URI"))
        db_name = crawler.settings.get("MONGO_DB", "crawler_db")
        return cls(mongo_uri, db_name)

    def process_item(self, item, spider):
        """
        Store scraped item into MongoDB (both raw_content and doc_metadata).
        """
        # Ensure UUID
        uuid_val = item.get("uuid") or str(uuid.uuid4())
        item["uuid"] = uuid_val

        now_iso = datetime.utcnow().isoformat()

        crawl_info = {
            "spider_name": spider.name,
            "crawl_date": item.get("metadata", {}).get("crawl_date", now_iso),
        }

        # --- Store raw content ---
        raw_doc = {
            "_id": uuid_val,  # use UUID as MongoDB _id
            "url": item.get("url"),
            "title": item.get("title"),
            "content": item.get("content")
            or item.get("article")
            or item.get("full_poem")
            or "",
            "lang_labels": item.get("lang_labels", []),
            "lang_confidences": item.get("lang_confidences", []),
            "crawl_info": crawl_info,
            "updated_at": now_iso,
        }

        # --- Store metadata ---
        meta_doc = {
            "_id": uuid_val,  # use UUID as MongoDB _id
            "url": item.get("url"),
            "metadata": item.get("metadata", {}),
            "content_length": item.get("content_length"),
            "content_hash_md5": item.get("content_hash_md5"),
            "crawl_info": crawl_info,
            "updated_at": now_iso,
        }
        # Upsert (merge) both documents

        # Upsert (merge) both documents
        self.raw_collection.update_one(
            {"_id": uuid_val},
            {
                "$set": {k: v for k, v in raw_doc.items() if k != "created_at"},
                "$setOnInsert": {"created_at": now_iso},
            },
            upsert=True,
        )

        self.meta_collection.update_one(
            {"_id": uuid_val},
            {
                "$set": {k: v for k, v in meta_doc.items() if k != "created_at"},
                "$setOnInsert": {"created_at": now_iso},
            },
            upsert=True,
        )
        spider.logger.info(
            f"✅ Stored item UUID {uuid_val} in MongoDB ({self.db_name})")
        return item

    def close_spider(self, spider):
        """
        Gracefully close DB connection when spider finishes.
        """
        try:
            self.client.close()
            spider.logger.info("🔒 MongoDB connection closed.")
        except Exception as e:
            spider.logger.error(f"Failed to close MongoDB connection: {e}")
