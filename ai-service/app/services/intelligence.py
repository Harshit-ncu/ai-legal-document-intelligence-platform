# app/services/intelligence.py
# ─────────────────────────────────────────────────────────
# Document Intelligence Service
#
# WHY DOES THIS FILE EXIST?
#   This file orchestrates the entire intelligence pipeline.
#   It takes a file, delegates to the correct text extractor
#   (OCR or native text), cleans the text, calculates stats,
#   detects language, classifies the document, and logs the
#   metadata.
#
# HOW DOES IT WORK?
#   1. Routing: Uses file extension to pick the right extractor.
#   2. Processing: Passes the raw text through intelligence.py utilities.
#   3. Logging: Emits structured JSON-friendly logs (without sensitive text).
# ─────────────────────────────────────────────────────────

import time
import logging

from app.utils.ocr_helpers import extract_text as extract_with_ocr
from app.services.extractor import extract_docx_text, extract_txt_text
from app.utils.intelligence import (
    clean_text,
    calculate_document_statistics,
    detect_language,
    classify_document
)

# ── Structured Logging Setup ─────────────────────────────
# We configure a logger specific to this module.
logger = logging.getLogger("document_intelligence")
logger.setLevel(logging.INFO)
# Prevent duplicate logs if the handler is already attached
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def analyze_document(file_path: str, file_extension: str, original_filename: str) -> dict:
    """
    Main orchestration function for Feature 4.

    Args:
        file_path: Absolute path to the saved temp file.
        file_extension: Lowercase file extension (e.g. '.pdf', '.docx').
        original_filename: The original name of the file uploaded by the user.

    Returns:
        dict: Complete metadata and cleaned text matching the IntelligenceResponse schema.
    """
    start_time = time.perf_counter()
    ext = file_extension.lower()
    
    extraction_method = "unknown"
    ocr_used = False
    doc_type = ext.lstrip('.')
    raw_text = ""
    page_count = 1

    # ── Step 1: Text Extraction Routing ───────────────────
    if ext in (".pdf", ".jpg", ".jpeg", ".png"):
        extraction_method = "ocr_or_pdf_native"
        # Use Module 2B's master dispatcher which handles PDF detection and Image OCR
        extract_result = extract_with_ocr(file_path, ext)
        raw_text = extract_result["text"]
        ocr_used = extract_result["ocrUsed"]
        doc_type = extract_result["documentType"]
        page_count = extract_result["pageCount"]
        
    elif ext == ".docx":
        extraction_method = "docx_native"
        extract_result = extract_docx_text(file_path)
        raw_text = extract_result["text"]
        ocr_used = False
        doc_type = "docx"
        page_count = extract_result["pageCount"]
        
    elif ext == ".txt":
        extraction_method = "txt_native"
        extract_result = extract_txt_text(file_path)
        raw_text = extract_result["text"]
        ocr_used = False
        doc_type = "txt"
        page_count = extract_result["pageCount"]
        
    else:
        raise ValueError(f"Unsupported file extension '{ext}'")

    # ── Step 2: Document Intelligence Processing ─────────
    # Clean the raw text (remove extra spaces, fix line breaks)
    cleaned_text = clean_text(raw_text)
    
    # Calculate reading stats
    stats = calculate_document_statistics(cleaned_text)
    
    # Detect language and classification
    lang_name, lang_conf = detect_language(cleaned_text)
    class_name, class_conf = classify_document(cleaned_text)
    
    # Calculate elapsed time in ms
    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    # ── Step 3: Structured Logging ────────────────────────
    # We log the metadata but NOT the document contents.
    # We format this as a clear dictionary string for log parsers.
    log_data = {
        "filename": original_filename,
        "document_type": doc_type,
        "extraction_method": extraction_method,
        "ocr_used": ocr_used,
        "language": lang_name,
        "classification": class_name,
        "processing_time_ms": elapsed_ms
    }
    logger.info(f"Document Processed: {log_data}")

    # ── Step 4: Construct Return Dictionary ───────────────
    return {
        "documentType": doc_type,
        "classification": class_name,
        "classificationConfidence": class_conf,
        "ocrUsed": ocr_used,
        "pageCount": page_count,
        "wordCount": stats["wordCount"],
        "characterCount": stats["characterCount"],
        "paragraphCount": stats["paragraphCount"],
        "sentenceCount": stats["sentenceCount"],
        "estimatedReadingTimeMinutes": stats["estimatedReadingTimeMinutes"],
        "language": lang_name,
        "languageConfidence": lang_conf,
        "processingTimeMs": elapsed_ms,
        "text": cleaned_text
    }
