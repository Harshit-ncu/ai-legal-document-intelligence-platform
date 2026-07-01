# app/utils/intelligence.py
# ─────────────────────────────────────────────────────────
# Reusable text processing module for Document Intelligence.
#
# WHY DOES THIS FILE EXIST?
#   Raw extracted text (from PDFs or OCR) is often messy. It
#   contains extra spaces, weird line breaks, and artifacts.
#   Also, future AI modules need basic facts (like word count,
#   language, and document type) before they can summarize or
#   extract clauses.
#
# HOW DOES IT WORK?
#   We split the intelligence pipeline into four single-responsibility
#   functions. Each function takes a string of text and returns
#   a specific piece of structured information.
# ─────────────────────────────────────────────────────────

import re
from langdetect import detect_langs, LangDetectException


# ─────────────────────────────────────────────────────────
# STEP 1: Text Cleaning
# ─────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """
    Cleans raw extracted text for downstream AI modules.

    Rules applied:
      1. Normalizes line endings (\r\n -> \n)
      2. Replaces 3 or more consecutive newlines with exactly 2
         (preserves paragraph breaks but removes huge gaps)
      3. Replaces multiple horizontal spaces/tabs with a single space
      4. Strips leading and trailing whitespace

    Args:
        text: The raw text string.

    Returns:
        Cleaned text string.
    """
    if not text:
        return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n")

    # Replace 3 or more newlines with exactly 2 (preserves paragraphs)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Replace multiple spaces/tabs within a line with a single space
    # [ \t]+ matches one or more spaces or tabs
    text = re.sub(r'[ \t]+', ' ', text)

    return text.strip()


# ─────────────────────────────────────────────────────────
# STEP 2: Document Statistics
# ─────────────────────────────────────────────────────────

def calculate_document_statistics(text: str) -> dict:
    """
    Calculates basic statistics about the document.

    HOW WE COUNT:
      - words: splitting by any whitespace.
      - characters: total length of the string.
      - paragraphs: splitting by double newlines (\n\n).
      - sentences: a basic regex splitting on '.', '!', or '?'.
      - reading time: average adult reading speed is ~238 words per minute.

    Args:
        text: The cleaned text string.

    Returns:
        dict: wordCount, characterCount, paragraphCount,
              sentenceCount, estimatedReadingTimeMinutes
    """
    if not text:
        return {
            "wordCount": 0,
            "characterCount": 0,
            "paragraphCount": 0,
            "sentenceCount": 0,
            "estimatedReadingTimeMinutes": 0
        }

    # Word count
    words = text.split()
    word_count = len(words)

    # Character count
    character_count = len(text)

    # Paragraph count (split by 2 or more newlines)
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    paragraph_count = len(paragraphs)

    # Sentence count (split by . ! ?)
    # This is a simple heuristic. NLP libraries like spaCy are better,
    # but this is fast and sufficient for basic stats.
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if s.strip()]
    sentence_count = len(sentences)

    # Estimated reading time (based on 238 WPM)
    # Use max(1, ...) to ensure it always says at least 1 minute if there are words.
    estimated_time = max(1, round(word_count / 238)) if word_count > 0 else 0

    return {
        "wordCount": word_count,
        "characterCount": character_count,
        "paragraphCount": paragraph_count,
        "sentenceCount": sentence_count,
        "estimatedReadingTimeMinutes": estimated_time
    }


# ─────────────────────────────────────────────────────────
# STEP 3: Language Detection
# ─────────────────────────────────────────────────────────

# A small map to convert ISO 639-1 codes to human readable names.
# Expand this as needed.
LANGUAGE_MAP = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "zh-cn": "Chinese",
    "ja": "Japanese"
}

def detect_language(text: str) -> tuple[str, float]:
    """
    Detects the primary language of the text.

    Uses 'langdetect', a Python port of Google's language-detection library.
    It returns a list of probabilities for different languages.

    Returns:
        tuple: (language_name, confidence_score)
               e.g. ("English", 0.99)
    """
    if not text.strip():
        return "Unknown", 0.0

    try:
        # detect_langs returns a list of Language objects, sorted by probability
        # e.g. [en:0.999996, es:0.000003]
        langs = detect_langs(text)
        if not langs:
            return "Unknown", 0.0

        top_lang = langs[0]
        lang_code = top_lang.lang
        confidence = round(top_lang.prob, 2)

        lang_name = LANGUAGE_MAP.get(lang_code, lang_code)
        return lang_name, confidence

    except LangDetectException:
        # Happens if text has no letters (e.g. all numbers or symbols)
        return "Unknown", 0.0


# ─────────────────────────────────────────────────────────
# STEP 4: Basic Document Classification
# ─────────────────────────────────────────────────────────

# Keywords that strongly indicate a specific document type.
# We use sets for fast O(1) lookups.
CLASSIFICATION_RULES = {
    "NDA": {"non-disclosure", "confidentiality", "disclosing party", "receiving party", "trade secret"},
    "Employment Agreement": {"salary", "employment", "employee", "employer", "severance", "vacation"},
    "Lease Agreement": {"tenant", "landlord", "lease", "rent", "premises", "sublet"},
    "Service Agreement": {"contractor", "client", "services", "statement of work", "deliverables"},
    "Purchase Agreement": {"buyer", "seller", "purchase price", "closing date", "goods"},
    "Privacy Policy": {"personal data", "cookies", "privacy", "gdpr", "ccpa", "information we collect"},
    "Terms & Conditions": {"terms of service", "user agreement", "limitation of liability", "indemnification", "governing law"}
}

def classify_document(text: str) -> tuple[str, float]:
    """
    Classifies a document based on simple keyword heuristics.

    HOW IT WORKS:
      We count how many unique keywords from our rule sets appear
      in the text. The category with the most keyword matches wins.
      Confidence is calculated based on how many keywords matched.

    WHY RULES INSTEAD OF AI?
      AI (LLMs) are slow and expensive. Running a simple regex/keyword
      check first is virtually free. If the rules are highly confident,
      we don't need AI. If they are unsure, we could trigger an AI
      fallback later (Module 3).

    Args:
        text: The cleaned document text.

    Returns:
        tuple: (document_type, confidence_score)
               e.g. ("NDA", 0.85)
    """
    if not text:
        return "Unknown", 0.0

    text_lower = text.lower()
    scores = {}

    for doc_type, keywords in CLASSIFICATION_RULES.items():
        # Count how many keywords appear at least once
        matches = sum(1 for kw in keywords if kw in text_lower)
        if matches > 0:
            # Score is the percentage of keywords that were found
            # (matches / total keywords for that category)
            scores[doc_type] = matches / len(keywords)

    if not scores:
        return "Unknown", 0.0

    # Find the document type with the highest score
    best_match = max(scores.items(), key=lambda item: item[1])
    doc_type, confidence = best_match

    # Round confidence to 2 decimal places
    return doc_type, round(confidence, 2)
