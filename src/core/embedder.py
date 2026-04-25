import requests
import json
import os
import hashlib
from config.logger import get_logger
from config.settings import EMBEDDINGS_CACHE_FILE, OLLAMA_API_URL, EMBEDDING_MODEL
from tenacity import retry, wait_exponential, stop_after_attempt

logger = get_logger("embedder")

def load_cache():
    if os.path.exists(EMBEDDINGS_CACHE_FILE):
        try:
            with open(EMBEDDINGS_CACHE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return {}
    return {}

def save_cache(cache):
    with open(EMBEDDINGS_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f)

cache = load_cache()

def get_key(text):
    return hashlib.md5(text.encode()).hexdigest()

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
def get_embedding(text):
    key = get_key(text)

    if key in cache:
        return cache[key]

    try:
        res = requests.post(
            f"{OLLAMA_API_URL}/api/embeddings",
            json={
                "model": EMBEDDING_MODEL,
                "prompt": text
            },
            timeout=10
        )
        res.raise_for_status()
        data = res.json()

        if "embedding" not in data:
            logger.error("Invalid embedding response")
            raise ValueError("No embedding in response")

        emb = data["embedding"]
        cache[key] = emb

        return emb

    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        # Re-raise to trigger tenacity, fallback handled later if it completely fails
        raise e
