# ArabicEduCrawler-Code

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Scrapy](https://img.shields.io/badge/Scrapy-Crawler-green.svg)](https://scrapy.org/)
[![Playwright](https://img.shields.io/badge/Playwright-Chromium-orange.svg)](https://playwright.dev/python/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Database-brightgreen.svg)](https://www.mongodb.com/)

ArabicEduCrawler-Code is a focused web crawling framework for collecting Arabic educational content from heterogeneous websites. It combines Scrapy, Playwright-based browser rendering, FastText language filtering, domain-specific extraction logic, metadata preservation, and MongoDB storage to build a clean, traceable corpus for downstream NLP and semantic retrieval tasks.

This repository contains the crawling component used in the AraEduSSE framework.

## Overview

The crawler is designed for Arabic educational corpus construction rather than general web scraping. It targets selected domains, respects site structure through site-specific extraction rules, renders JavaScript-heavy pages when needed, filters low-quality and non-Arabic content during crawling, and stores both raw text and metadata for each accepted document.

The current implementation includes focused spiders for:

- `alukah.net`
- `ar.wikipedia.org`
- `adab.com`
- `shamela.ws`

## Main Features

- Focused crawling over selected Arabic educational domains
- Scrapy-based crawling with Playwright rendering for dynamic pages
- Site-specific extraction rules stored in JSON configuration
- Online FastText-based Arabic language filtering
- Dual-threshold language acceptance strategy
- Duplicate detection using normalized content + URL hashing
- Minimum-length filtering
- Metadata extraction and storage
- MongoDB persistence for both raw content and document metadata
- Aggregated crawl statistics export

## Architecture

The crawling workflow is:

1. Start from curated seed URLs in the site configuration
2. Crawl pages using Scrapy
3. Render JavaScript-heavy pages through Playwright when required
4. Extract page content using site-specific rules
5. Filter short, duplicate, or non-Arabic pages
6. Extract metadata
7. Store accepted items in MongoDB
8. Export crawl summary statistics at the end of the run

## Requirements

- Python 3.11+
- MongoDB
- Chromium via Playwright

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/afyaa-alkhamisi/ArabicEduCrawler-Code.git
cd ArabicEduCrawler-Code
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

### 3. Start MongoDB

Make sure MongoDB is running locally or in Docker.

### 4. Run the crawler

```bash
python crawler/main.py
```

## Docker Usage

If you package this service in Docker, the crawler entrypoint is:

```bash
./entrypoint.sh
```

The entrypoint:

- installs Playwright Chromium if not already cached
- installs `scrapy-playwright`
- starts the crawler

## Docker Run

### Build the image

```bash
docker build -t arabiceducrawler .
```

### Run with MongoDB connection

```bash
docker run --rm \
  -e MONGO_URI="mongodb://mongoadmin:mongoadmin@host.docker.internal:27017/?authSource=admin" \
  -v "$(pwd):/app" \
  arabiceducrawler
```

## Repository Structure
```text
ArabicEduCrawler-Code/
├── 2_crawler/
│   ├── configs/
│   │   └── sites_config.json
│   ├── extractors/
│   │   ├── custom_extractors1.py
│   │   ├── custom_extractors2.py
│   │   ├── custom_extractors3.py
│   │   └── custom_extractors4.py
│   ├── middlewares/
│   │   └── config_middleware.py
│   ├── pipelines/
│   │   ├── core_filter_pipeline.py
│   │   └── mongo_pipeline.py
│   ├── spiders/
│   │   ├── spider1.py
│   │   ├── spider2.py
│   │   ├── spider3.py
│   │   └── spider4.py
│   ├── utils/
│   │   ├── filters.py
│   │   └── metadata.py
│   ├── items.py
│   ├── main.py
│   └── settings.py
├── xpath_extraction.ipynb
├── entrypoint.sh
├── mongo_helper.py
├── requirements.txt
└── scrapy.cfg
```

### Adding a New Website

1. Add the domain configuration to `crawler/configs/sites_config.json`
2. Add or adapt a spider if needed
3. Add a custom extractor if the site needs specialized parsing
4. Test extraction, filtering, and MongoDB storage

### Notes

- This repository is designed for focused Arabic educational crawling, not for general-purpose web scraping.
- Some websites require Playwright rendering due to JavaScript-driven content.
- The project stores content and metadata separately to support traceability and downstream corpus construction.
- The final corpus-building and NLP annotation stages are performed outside this repository.

## Citation

If you use this dataset, please cite:

### APA

Alkhamisi, A. A., Bamashmoos, F., & Alsaggaf, W. (2026). *ArabicEduCrawler: AI-Assisted Focused Crawling and Corpus Construction for Arabic Educational Web Content*. Applied Sciences, 16(12), 5964. https://doi.org/10.3390/app16125964

### BibTeX

```bibtex
@Article{app16125964,
  AUTHOR = {Alkhamisi, Afyaa Atyan and Bamashmoos, Fatmah and Alsaggaf, Wafaa},
  TITLE = {ArabicEduCrawler: AI-Assisted Focused Crawling and Corpus Construction for Arabic Educational Web Content},
  JOURNAL = {Applied Sciences},
  VOLUME = {16},
  YEAR = {2026},
  NUMBER = {12},
  ARTICLE-NUMBER = {5964},
  URL = {https://www.mdpi.com/2076-3417/16/12/5964},
  ISSN = {2076-3417},
  DOI = {10.3390/app16125964}
}
```
