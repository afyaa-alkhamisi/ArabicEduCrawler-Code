#!/bin/bash
set -e

# --- Ensure Playwright browsers are installed ---
if [ ! -d "$PLAYWRIGHT_BROWSERS_PATH" ] || [ -z "$(ls -A $PLAYWRIGHT_BROWSERS_PATH)" ]; then
    echo "🎯 Installing Playwright browsers (Chromium)..."
    python -m playwright install chromium
else
    echo "✅ Chromium already installed, using cached version"
fi

# --- Install Scrapy Playwright dependencies ---
# (needed for the middleware to work correctly)
python -m pip install --no-cache-dir scrapy-playwright

# --- Run the crawler ---
echo "🚀 Starting crawler..."
python crawler/main.py
