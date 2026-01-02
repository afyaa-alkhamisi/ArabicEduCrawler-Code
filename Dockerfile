FROM python:3.11-slim

WORKDIR /app

# --- System dependencies ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    cmake \
    curl \
    gnupg \
    ca-certificates \
    wget \
    unzip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# --- Copy requirements first ---
COPY requirements.txt .

# --- Upgrade pip & core build tools ---
RUN pip install --upgrade pip setuptools wheel cython

# --- Install numpy and FastText safely first ---
RUN pip install --no-cache-dir "numpy<2.0" fasttext-numpy2

# --- Install remaining requirements ---
RUN pip install --no-cache-dir -r requirements.txt

# --- Playwright dependencies ---
ENV PLAYWRIGHT_DOWNLOAD_HOST=https://playwright.azureedge.net
RUN python -m playwright install-deps && python -m playwright install chromium

# --- Pre-download FastText model ---
RUN mkdir -p /app/models && \
    python -c "from huggingface_hub import hf_hub_download; \
    hf_hub_download(repo_id='facebook/fasttext-language-identification', \
    filename='model.bin', cache_dir='/app/models')"

# --- Environment setup ---
ENV PYTHONPATH=/app
ENV PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright
#ENV MODEL_PATH=/app/models/facebook/fasttext-language-identification/model.bin

# --- Copy project code ---
COPY . .

# --- Entrypoint setup ---
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
