import importlib
import logging
import os
import re
import hashlib
import fasttext
from huggingface_hub import hf_hub_download
from pathlib import Path


# Set up logging
logger = logging.getLogger("fasttext_utils")
if not logger.handlers:  # prevent duplicate handlers
    handler = logging.FileHandler("fasttext_filter.log", encoding="utf-8")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def get_fasttext_version():
    for pkg in ["fasttext", "fasttext-numpy2", "fasttext-numpy2-wheel"]:
        try:
            return importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            continue
    return "unknown"


print("✅✅✅     FastText version:", get_fasttext_version(),    "✅✅✅")

MODEL_PATH = "/app/models/facebook/fasttext-language-identification/model.bin"


# Ensure the parent directory exists
os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

# Check if model exists, if not download it
if not os.path.isfile(MODEL_PATH):
    try:
        MODEL_PATH = hf_hub_download(
            repo_id="facebook/fasttext-language-identification",
            filename="model.bin",
            cache_dir=os.path.dirname(MODEL_PATH)
        )
        logger.info(f"Downloaded FastText model to {MODEL_PATH}")
    except Exception as e:
        logger.error(f"Failed to download FastText model: {e}")
        MODEL_PATH = None

# Load FastText model
FASTTEXT_MODEL = None
if MODEL_PATH and os.path.isfile(MODEL_PATH):
    try:
        FASTTEXT_MODEL = fasttext.load_model(MODEL_PATH)
        logger.info("FastText model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load FastText model: {e}")


def normalize_arabic_text(text):
    """
    Remove Arabic diacritics and non-letter marks
    before passing text to FastText — to fix misclassification.
    """
    text = re.sub(r"[ًٌٍَُِّْـ]", "", text)  # remove diacritics (tashkeel)
    text = re.sub(r"[إأٱآا]", "ا", text)  # normalize alef variants
    text = re.sub(r"ى", "ي", text)  # convert alef maqsura to ya
    text = re.sub(r"ؤ", "و", text)
    text = re.sub(r"ئ", "ي", text)
    text = re.sub(r"ة", "ه", text)
    text = re.sub(r"\s+", " ", text)  # normalize spacing
    text = re.sub(r"[\[\]]", "", text)
    text = re.sub(r"[\/\d]+", " ", text)  # remove slashes and numbers
    return text.strip()


def normalize_for_dedup(text):
    text = text.lower()
    text = re.sub(r"[ًٌٍَُِّْـ]", "", text)  # remove diacritics
    text = re.sub(r"\s+", " ", text)  # normalize whitespace
    text = text.strip()
    return text


def is_arabic(text, threshold=0.8, top_k=3, alt_threshold=0.5):
    """
    Returns True if 'text' is confidently identified as Arabic.
    - threshold: main confidence threshold for top prediction
    - min_length: minimum number of characters required in the text
    - top_k: consider Arabic in top_k predictions with lower alt_threshold
    - alt_threshold: secondary (lower) threshold for Arabic in top_k
    """
    if not FASTTEXT_MODEL:
        logger.error("FastText model not loaded.")
        return {"is_arabic": False, "reason": "FastText model not loaded.", "labels": [], "confidences": []}

    # Fallback for very short text (<20 chars)
    if not text or len(text.strip()) < 10:
        # logger.info("Text too short for reliable language detection.")
        return {"is_arabic": False, "reason": "Text too short for reliable language detection", "labels": [], "confidences": []}

    # Normalize whitespace
    text = text.replace("\r", " ").replace("\n", " ")

    try:
        labels, confidences = FASTTEXT_MODEL.predict(text, k=top_k)
        confidences = [float(c) for c in confidences]
        arabic_labels = {
            "__label__ar", "__label__ara", "__label__arb",
            "__label__ar_Arab", "__label__arb_Arab",
            "__label__ara_Arab", "__label__ar-Arabic",
        }

        # Primary threshold: Arabic as top prediction
        if labels[0] in arabic_labels and confidences[0] >= threshold:
            # logger.info(f"Arabic as top prediction ({confidences[0]:.2f}).")
            return {"is_arabic": True, "reason": "Arabic as top prediction ", "labels": list(labels), "confidences": confidences}

        # Secondary threshold: Arabic in top_k predictions
        for lbl, conf in zip(labels, confidences):
            if lbl in arabic_labels and conf >= alt_threshold:
                # logger.info(
                #    f"Arabic found in top-{top_k} predictions ({conf:.2f}).")
                return {"is_arabic": True, "reason": f"Arabic found in top-{top_k}", "labels": list(labels), "confidences": confidences}

        # Not Arabic
        # logger.info(
        #    f"Arabic not confidently detected. Confidences: {confidences}")
        return {"is_arabic": False, "reason": "Arabic not confidently detected.", "labels": list(labels), "confidences": confidences}

    except Exception as e:
        logger.error(f"Error during FastText prediction: {e}")
        return {"is_arabic": False, "reason": "Error during FastText prediction.", "labels": [], "confidences": []}


"""Check for duplicate content using MD5 hash."""


def get_md5_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


# def is_duplicate(md5_hash: str, seen_hashes: set) -> bool:
#    return md5_hash in seen_hashes
