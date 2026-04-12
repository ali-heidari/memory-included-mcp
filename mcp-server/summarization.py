"""Text summarization for conversation memory"""

import logging
from config import SUMMARY_RULES, SUMMARIZATION_MAX_LENGTH, SUMMARIZATION_MIN_LENGTH

logger = logging.getLogger(__name__)

# Lazy load transformer model
_summarization_pipeline = None


def get_summarizer():
    """Lazy load text summarization pipeline"""
    global _summarization_pipeline
    if _summarization_pipeline is None:
        try:
            from transformers import pipeline

            logger.info("Loading summarization model (facebook/bart-large-cnn)")
            _summarization_pipeline = pipeline("summarization", model="facebook/bart-large-cnn")
            logger.info("Summarization model loaded successfully")
        except ImportError:
            logger.warning("transformers library not installed. Install with: pip install transformers")
            return None
    return _summarization_pipeline


def extractive_summary(text: str, num_sentences: int = 2) -> str:
    """Simple extractive summarization (fallback)

    Args:
        text: Text to summarize
        num_sentences: Number of sentences to extract

    Returns:
        Extracted summary
    """
    sentences = text.split(".")
    sentences = [s.strip() for s in sentences if s.strip()]

    if len(sentences) <= num_sentences:
        return text

    # Simple: take first and last sentences
    summary = sentences[0] + ". " + sentences[-1] + "."
    return summary


def abstractive_summary(text: str, max_length: int, min_length: int) -> str:
    """Generate abstractive summary using transformer model

    Args:
        text: Text to summarize
        max_length: Maximum summary length
        min_length: Minimum summary length

    Returns:
        Generated summary or None if model unavailable
    """
    try:
        summarizer = get_summarizer()
        if summarizer is None:
            return None

        # Skip very short texts
        if len(text.split()) < 30:
            return None

        # Generate summary
        summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)

        if summary and len(summary) > 0:
            return summary[0]["summary_text"]

        return None

    except Exception as e:
        logger.error(f"Error in abstractive summarization: {e}")
        return None


def get_summary_config(text_length: int) -> dict:
    """Determine summary configuration based on text length

    Args:
        text_length: Character count of text

    Returns:
        Dict with summary_length and rules
    """
    for key, config in SUMMARY_RULES.items():
        if text_length <= config["max_chars"]:
            return config

    return SUMMARY_RULES["long"]


def summarize(text: str) -> str:
    """Auto-summarize text with intelligent fallback

    Strategy:
    1. For very short text (<100 chars): return as-is
    2. Try abstractive summarization first
    3. Fall back to extractive if abstractive fails
    4. Adjust length based on input length

    Args:
        text: Text to summarize

    Returns:
        Summary string
    """
    if not text or len(text.strip()) == 0:
        return ""

    # For very short texts, return as-is
    if len(text) < 100:
        return text.strip()

    # Get appropriate summary length
    config = get_summary_config(len(text))
    summary_length = config["summary_length"]

    # Try abstractive first
    abstract_summary = abstractive_summary(
        text, max_length=summary_length, min_length=max(15, summary_length // 2)
    )

    if abstract_summary:
        return abstract_summary

    # Fall back to extractive
    extract_summary = extractive_summary(text, num_sentences=2)

    if extract_summary and len(extract_summary) <= summary_length * 3:
        return extract_summary

    # Last resort: truncate to summary length with ellipsis
    if len(text) > summary_length:
        return text[: summary_length - 3].rsplit(" ", 1)[0] + "..."

    return text


def quality_score(original: str, summary: str) -> float:
    """Estimate summarization quality

    Returns float 0-1 where 1 is perfect compression

    Args:
        original: Original text
        summary: Summarized text

    Returns:
        Quality score
    """
    if not original or len(original) == 0:
        return 0.0

    compression_ratio = len(summary) / len(original)

    # Ideal compression: 30-50% of original
    if 0.3 <= compression_ratio <= 0.5:
        return 1.0
    elif 0.2 <= compression_ratio <= 0.7:
        return 0.8
    elif 0.1 <= compression_ratio <= 0.9:
        return 0.6
    else:
        return 0.3
