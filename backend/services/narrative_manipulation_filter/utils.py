"""
Utility Functions for Cognitive Defense System.

Collection of helper functions for text processing, hashing,
URL parsing, similarity computation, and adversarial robustness.
"""

from datetime import datetime, timedelta
import hashlib
import logging
import re
import string
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse, urlunparse

import numpy as np
from scipy.spatial.distance import cosine

logger = logging.getLogger(__name__)


# ============================================================================
# TEXT PROCESSING
# ============================================================================


def clean_text(text: str) -> str:
    """
    Clean and normalize text for analysis.

    Args:
        text: Raw input text

    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove zero-width characters (potential steganography)
    text = re.sub(r"[\u200b-\u200f\u202a-\u202e\ufeff]", "", text)

    # Normalize quotes
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2018", "'").replace("\u2019", "'")

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def extract_sentences(text: str) -> List[str]:
    """
    Split text into sentences.

    Args:
        text: Input text

    Returns:
        List of sentences
    """
    # Simple sentence splitting (production should use spaCy/NLTK)
    pattern = r"(?<=[.!?])\s+(?=[A-Z])"
    sentences = re.split(pattern, text)
    return [s.strip() for s in sentences if s.strip()]


def detect_all_caps_ratio(text: str) -> float:
    """
    Calculate ratio of uppercase letters (shouting indicator).

    Args:
        text: Input text

    Returns:
        Ratio of uppercase chars (0.0 to 1.0)
    """
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    uppercase_count = sum(1 for c in letters if c.isupper())
    return uppercase_count / len(letters)


def detect_excessive_punctuation(text: str) -> float:
    """
    Calculate ratio of punctuation marks (emotional manipulation indicator).

    Args:
        text: Input text

    Returns:
        Ratio of punctuation chars (0.0 to 1.0)
    """
    if not text:
        return 0.0
    punctuation_count = sum(1 for c in text if c in string.punctuation)
    return punctuation_count / len(text)


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text.

    Args:
        text: Input text

    Returns:
        List of URLs
    """
    url_pattern = r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)"
    return re.findall(url_pattern, text)


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL.

    Args:
        url: Full URL

    Returns:
        Domain name or None
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        # Remove www. prefix
        domain = re.sub(r"^www\.", "", domain)
        return domain.lower()
    except Exception as e:
        logger.error(f"Failed to extract domain from {url}: {e}")
        return None


def normalize_url(url: str) -> str:
    """
    Normalize URL for consistent comparison.

    Args:
        url: Raw URL

    Returns:
        Normalized URL
    """
    try:
        parsed = urlparse(url)
        # Remove trailing slashes, fragments, and query params
        normalized = urlunparse(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path.rstrip("/"),
                "",  # params
                "",  # query
                "",  # fragment
            )
        )
        return normalized
    except Exception:
        return url.lower()


# ============================================================================
# HASHING & FINGERPRINTING
# ============================================================================


def hash_text(text: str, algorithm: str = "sha256") -> str:
    """
    Generate cryptographic hash of text.

    Args:
        text: Input text
        algorithm: Hash algorithm (sha256, md5, sha1)

    Returns:
        Hex digest string
    """
    if algorithm == "sha256":
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    elif algorithm == "md5":
        return hashlib.md5(text.encode("utf-8")).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(text.encode("utf-8")).hexdigest()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")


def minhash_fingerprint(text: str, num_hashes: int = 128) -> List[int]:
    """
    Generate MinHash fingerprint for near-duplicate detection.

    Args:
        text: Input text
        num_hashes: Number of hash functions

    Returns:
        MinHash signature (list of integers)
    """
    # Simple MinHash implementation (production should use datasketch library)
    words = set(text.lower().split())
    if not words:
        return [0] * num_hashes

    signature = []
    for i in range(num_hashes):
        min_hash = float("inf")
        for word in words:
            # Combine word with seed
            hash_val = int(hashlib.md5(f"{word}_{i}".encode()).hexdigest(), 16)
            min_hash = min(min_hash, hash_val)
        signature.append(min_hash)

    return signature


def jaccard_similarity(set1: Set, set2: Set) -> float:
    """
    Calculate Jaccard similarity between two sets.

    Args:
        set1: First set
        set2: Second set

    Returns:
        Similarity score (0.0 to 1.0)
    """
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0

    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def minhash_jaccard_estimate(sig1: List[int], sig2: List[int]) -> float:
    """
    Estimate Jaccard similarity from MinHash signatures.

    Args:
        sig1: First MinHash signature
        sig2: Second MinHash signature

    Returns:
        Estimated Jaccard similarity
    """
    if len(sig1) != len(sig2):
        raise ValueError("MinHash signatures must have same length")

    matches = sum(1 for h1, h2 in zip(sig1, sig2) if h1 == h2)
    return matches / len(sig1)


# ============================================================================
# SIMILARITY & EMBEDDINGS
# ============================================================================


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First embedding vector
        vec2: Second embedding vector

    Returns:
        Similarity score (-1.0 to 1.0)
    """
    if vec1.shape != vec2.shape:
        raise ValueError("Vectors must have same dimensions")

    # Avoid division by zero
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return 1.0 - cosine(vec1, vec2)


def semantic_similarity_batch(
    query_embedding: np.ndarray, candidate_embeddings: np.ndarray, top_k: int = 5
) -> List[Tuple[int, float]]:
    """
    Find top-k most similar embeddings using cosine similarity.

    Args:
        query_embedding: Query vector (1D)
        candidate_embeddings: Matrix of candidate vectors (2D)
        top_k: Number of top results

    Returns:
        List of (index, similarity_score) tuples
    """
    similarities = []
    for i, candidate in enumerate(candidate_embeddings):
        sim = cosine_similarity(query_embedding, candidate)
        similarities.append((i, sim))

    # Sort by similarity descending
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]


# ============================================================================
# ADVERSARIAL ROBUSTNESS
# ============================================================================


def detect_homoglyph_attack(text: str) -> Tuple[bool, List[str]]:
    """
    Detect potential homoglyph/lookalike character attacks.

    Args:
        text: Input text

    Returns:
        (is_suspicious, list_of_suspicious_chars)
    """
    # Common homoglyph patterns
    suspicious_chars = []

    # Cyrillic lookalikes
    cyrillic_homoglyphs = {
        "\u0430": "a",  # Cyrillic 'a'
        "\u0435": "e",  # Cyrillic 'e'
        "\u043e": "o",  # Cyrillic 'o'
        "\u0440": "p",  # Cyrillic 'p'
        "\u0441": "c",  # Cyrillic 'c'
        "\u0445": "x",  # Cyrillic 'x'
    }

    for char in text:
        if char in cyrillic_homoglyphs:
            suspicious_chars.append(f"{char} (looks like {cyrillic_homoglyphs[char]})")

    # Check for mixed scripts (suspicious)
    has_latin = any(
        "\u0041" <= c <= "\u005a" or "\u0061" <= c <= "\u007a" for c in text
    )
    has_cyrillic = any("\u0400" <= c <= "\u04ff" for c in text)

    is_suspicious = len(suspicious_chars) > 0 or (has_latin and has_cyrillic)
    return is_suspicious, suspicious_chars


def add_adversarial_noise(
    text: str, perturbation_type: str = "char_swap", intensity: float = 0.05
) -> str:
    """
    Add adversarial perturbations for robustness testing.

    Args:
        text: Original text
        perturbation_type: 'char_swap', 'char_delete', 'char_insert'
        intensity: Perturbation ratio (0.0 to 1.0)

    Returns:
        Perturbed text
    """
    import random

    chars = list(text)
    num_perturbations = max(1, int(len(chars) * intensity))

    for _ in range(num_perturbations):
        if not chars:
            break

        idx = random.randint(0, len(chars) - 1)

        if perturbation_type == "char_swap" and idx < len(chars) - 1:
            chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
        elif perturbation_type == "char_delete":
            chars.pop(idx)
        elif perturbation_type == "char_insert":
            chars.insert(idx, random.choice(string.ascii_lowercase))

    return "".join(chars)


def randomized_smoothing_predict(
    base_text: str,
    prediction_func,
    num_samples: int = 100,
    noise_intensity: float = 0.02,
) -> Tuple[str, float]:
    """
    Certified adversarial robustness via randomized smoothing.

    Args:
        base_text: Original text
        prediction_func: Model prediction function
        num_samples: Number of noise samples
        noise_intensity: Perturbation strength

    Returns:
        (predicted_class, confidence)
    """
    predictions = []

    for _ in range(num_samples):
        noisy_text = add_adversarial_noise(base_text, "char_swap", noise_intensity)
        pred = prediction_func(noisy_text)
        predictions.append(pred)

    # Majority vote
    from collections import Counter

    vote_counts = Counter(predictions)
    most_common = vote_counts.most_common(1)[0]

    predicted_class = most_common[0]
    confidence = most_common[1] / num_samples

    return predicted_class, confidence


# ============================================================================
# TEMPORAL & STATISTICAL UTILS
# ============================================================================


def exponential_decay_weight(timestamp: datetime, half_life_days: int = 30) -> float:
    """
    Calculate exponential decay weight for temporal scoring.

    Args:
        timestamp: Event timestamp
        half_life_days: Half-life in days

    Returns:
        Weight (0.0 to 1.0)
    """
    age_days = (datetime.utcnow() - timestamp).days
    decay_rate = np.log(2) / half_life_days
    weight = np.exp(-decay_rate * age_days)
    return weight


def bayesian_update(
    prior: float, likelihood_true: float, likelihood_false: float
) -> float:
    """
    Bayesian belief update.

    Args:
        prior: Prior probability
        likelihood_true: P(evidence | hypothesis is true)
        likelihood_false: P(evidence | hypothesis is false)

    Returns:
        Posterior probability
    """
    numerator = likelihood_true * prior
    denominator = likelihood_true * prior + likelihood_false * (1 - prior)
    return numerator / denominator if denominator > 0 else prior


def beta_distribution_credibility(alpha: float, beta: float) -> float:
    """
    Calculate credibility score from Beta distribution parameters.

    Args:
        alpha: Success count + 1
        beta: Failure count + 1

    Returns:
        Expected credibility (0.0 to 1.0)
    """
    return alpha / (alpha + beta)


def wilson_score_interval(
    successes: int, total: int, confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate Wilson score confidence interval.

    More reliable than simple proportion for small sample sizes.

    Args:
        successes: Number of successes
        total: Total trials
        confidence: Confidence level (default 95%)

    Returns:
        (lower_bound, upper_bound)
    """
    if total == 0:
        return (0.0, 0.0)

    from scipy.stats import norm

    p_hat = successes / total
    z = norm.ppf((1 + confidence) / 2)

    denominator = 1 + z**2 / total
    center = (p_hat + z**2 / (2 * total)) / denominator
    margin = (
        z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * total)) / total) / denominator
    )

    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)

    return (lower, upper)


# ============================================================================
# VALIDATION & SANITIZATION
# ============================================================================


def validate_url(url: str) -> bool:
    """
    Validate URL format.

    Args:
        url: URL string

    Returns:
        True if valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def sanitize_for_sparql(text: str) -> str:
    """
    Sanitize text for SPARQL query injection prevention.

    Args:
        text: User input text

    Returns:
        Sanitized text
    """
    # Escape special SPARQL characters
    text = text.replace("\\", "\\\\")
    text = text.replace('"', '\\"')
    text = text.replace("\n", "\\n")
    text = text.replace("\r", "\\r")
    return text


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Input text
        max_length: Maximum length
        suffix: Truncation suffix

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


# ============================================================================
# LOGGING & DEBUGGING
# ============================================================================


def log_execution_time(func):
    """
    Decorator to log function execution time.

    Usage:
        @log_execution_time
        async def my_function():
            pass
    """
    import functools
    import time

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = (time.time() - start) * 1000
        logger.debug(f"{func.__name__} executed in {elapsed:.2f}ms")
        return result

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = (time.time() - start) * 1000
        logger.debug(f"{func.__name__} executed in {elapsed:.2f}ms")
        return result

    import asyncio

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
