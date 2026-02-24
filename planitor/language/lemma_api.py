"""
HTTP client for lemma.solberg.is - Icelandic lemmatization API.

This replaces the heavy Greynir-based lemmatization with a lightweight HTTP API,
significantly reducing memory usage in worker processes.
"""

import logging
import os
from typing import List, Optional

import requests

logger = logging.getLogger(__name__)

LEMMA_API_URL = "https://lemma.solberg.is"
LEMMA_API_KEY = os.environ.get("LEMMA_API_KEY")  # Optional: bypasses rate limiting
TIMEOUT = 30  # seconds


def _get_headers() -> dict:
    """Get request headers, including API key if configured."""
    headers = {"Content-Type": "application/json"}
    if LEMMA_API_KEY:
        headers["X-API-Key"] = LEMMA_API_KEY
    return headers


def lemmatize_text(text: str) -> List[str]:
    """
    Lemmatize text and return unique lemmas.
    
    Uses the /api/text endpoint which handles tokenization and returns
    unique lemmas suitable for search indexing.
    """
    if not text or not text.strip():
        return []
    
    try:
        response = requests.post(
            f"{LEMMA_API_URL}/api/text",
            json={"text": text},
            headers=_get_headers(),
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("lemmas", [])
    except requests.RequestException as e:
        logger.error(f"Lemma API error: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error calling lemma API: {e}")
        return []


def lemmatize_word(word: str) -> List[str]:
    """
    Lemmatize a single word and return its lemmas.
    
    Uses the /api/lemmatize endpoint for single word lookups.
    """
    if not word or not word.strip():
        return []
    
    try:
        response = requests.post(
            f"{LEMMA_API_URL}/api/lemmatize",
            json={"word": word},
            headers=_get_headers(),
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("lemmas", [])
    except requests.RequestException as e:
        logger.error(f"Lemma API error for word '{word}': {e}")
        return [word]  # Fallback to original word
    except Exception as e:
        logger.error(f"Unexpected error calling lemma API: {e}")
        return [word]


def lemmatize_batch(words: List[str]) -> List[dict]:
    """
    Lemmatize multiple words in a single request.
    
    Uses the /api/batch endpoint for efficient batch processing.
    Returns list of {"word": str, "lemmas": List[str]} dicts.
    """
    if not words:
        return []
    
    # API limit is 1000 words per batch
    words = words[:1000]
    
    try:
        response = requests.post(
            f"{LEMMA_API_URL}/api/batch",
            json={"words": words},
            headers=_get_headers(),
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except requests.RequestException as e:
        logger.error(f"Lemma API batch error: {e}")
        return [{"word": w, "lemmas": [w]} for w in words]
    except Exception as e:
        logger.error(f"Unexpected error calling lemma API: {e}")
        return [{"word": w, "lemmas": [w]} for w in words]
