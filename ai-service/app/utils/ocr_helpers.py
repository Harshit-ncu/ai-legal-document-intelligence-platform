# app/utils/ocr_helpers.py
# ─────────────────────────────────────────────────────────
# OCR utility functions for Module 2B.
#
# WHY DOES THIS FILE EXIST?
#   All the actual work happens here — detecting PDF type,
#   running Tesseract, converting pages to images.
#   Zero HTTP code lives here. These are pure functions:
#   give them a file path, they return a result dict.
#
# WHY PUT UTILITIES IN utils/ NOT services/?
#   services/extractor.py is the "primary" text extraction
#   service (Module 2A). OCR helpers are building blocks
#   that the OCR service (services/ocr.py) calls internally.
#   utils/ = low-level helpers; services/ = orchestration.
#
# SINGLE RESPONSIBILITY PRINCIPLE:
#   Each function does exactly ONE thing:
#   - detect_pdf_type()                  → is it searchable or scanned?
#   - extract_text_from_image()          → one image → OCR text
#   - extract_text_from_scanned_pdf()    → scanned PDF → OCR all pages
#   - extract_text_from_searchable_pdf() → delegate to Module 2A
#   - extract_text()                     → master dispatcher
# ─────────────────────────────────────────────────────────

import os
import shutil                    # to check if 'tesseract' binary exists
from pathlib import Path
from typing import Literal

import fitz                      # PyMuPDF
import pytesseract               # Python wrapper around Tesseract CLI
from PIL import Image            # Pillow — image handling
from pdf2image import convert_from_path  # PDF page → PIL Image

# Reuse Module 2A's extract_pdf_text — no code duplication
from app.services.extractor import extract_pdf_text


# ─────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────

# Minimum number of characters on a page before we consider
# it "text-bearing". If PyMuPDF extracts fewer than this many
# characters from a page, the page is treated as image-only.
# Why 50? A real page of text has hundreds of characters.
# 50 is a generous lower bound that catches mostly-blank pages
# and pages where PyMuPDF extracted just a few stray characters
# from embedded watermarks or decorative elements.
MIN_CHARS_PER_PAGE = 50

# Tesseract language code for English.
# For multi-language: "eng+fra" or "eng+deu" etc.
TESSERACT_LANG = "eng"

# DPI for PDF-to-image conversion.
# 300 DPI is the industry standard for OCR — good balance of
# accuracy vs file size. Below 200 DPI → accuracy drops badly.
# Above 400 DPI → much larger images, slower, marginal gain.
PDF_DPI = 300


# ─────────────────────────────────────────────────────────
# HELPER: Verify Tesseract is installed
# ─────────────────────────────────────────────────────────

def _verify_tesseract() -> None:
    """
    Check that the Tesseract binary is accessible on this machine.

    WHY CHECK THIS?
      pytesseract is just a Python wrapper — it calls the real
      Tesseract C++ binary via subprocess. If Tesseract isn't
      installed (brew install tesseract), pytesseract fails with
      a confusing FileNotFoundError. We check early and give a
      clear, actionable error message.

    Raises:
        RuntimeError: if Tesseract binary is not found in PATH.
    """
    if shutil.which("tesseract") is None:
        raise RuntimeError(
            "Tesseract OCR is not installed or not in PATH. "
            "Install it with: brew install tesseract  (macOS) "
            "or: sudo apt install tesseract-ocr  (Linux)"
        )


# ─────────────────────────────────────────────────────────
# FUNCTION 1: detect_pdf_type()
# ─────────────────────────────────────────────────────────

def detect_pdf_type(file_path: str) -> Literal["searchable", "scanned"]:
    """
    Detect whether a PDF contains real embedded text (searchable)
    or only page images (scanned).

    HOW IT WORKS:
      We open the PDF with PyMuPDF and check a sample of pages.
      For each sample page, we call page.get_text() to extract
      whatever text PyMuPDF can find.

      If the total text across sample pages is substantial
      (more than MIN_CHARS_PER_PAGE characters on average),
      we call it "searchable".

      If the total text is tiny or zero, the pages are image-only
      → we call it "scanned".

    WHY SAMPLE INSTEAD OF ALL PAGES?
      A 200-page document would be slow to check every page.
      Checking the first few pages is fast and reliable — if
      the first 5 pages have embedded text, the whole PDF does.

    WHY NOT CHECK MIME TYPE?
      Both searchable and scanned PDFs have MIME type
      "application/pdf". The only way to know is to look inside.

    Args:
        file_path: Absolute path to a .pdf file.

    Returns:
        "searchable" or "scanned"

    Raises:
        ValueError: if the file cannot be opened as a PDF.
    """
    try:
        doc = fitz.open(file_path)
    except Exception as e:
        raise ValueError(f"Cannot open PDF: {e}")

    with doc:
        total_pages = len(doc)
        if total_pages == 0:
            raise ValueError("PDF has no pages.")

        # Sample up to 5 pages (or fewer for short documents)
        sample_size = min(5, total_pages)
        total_chars = 0

        for page_num in range(sample_size):
            page = doc[page_num]
            # get_text() returns "" for image-only pages
            text = page.get_text("text")
            total_chars += len(text.strip())

        # Average characters per sampled page
        avg_chars = total_chars / sample_size

    # If the average page has fewer than MIN_CHARS_PER_PAGE chars,
    # we treat the whole document as scanned.
    return "searchable" if avg_chars >= MIN_CHARS_PER_PAGE else "scanned"


# ─────────────────────────────────────────────────────────
# FUNCTION 2: extract_text_from_image()
# ─────────────────────────────────────────────────────────

def extract_text_from_image(image: Image.Image) -> str:
    """
    Run Tesseract OCR on a single Pillow Image object.

    HOW IT WORKS:
      1. Pillow (PIL) holds the image in memory as a grid of pixels.
      2. pytesseract.image_to_string() sends the image to the
         Tesseract binary via a temporary file.
      3. Tesseract analyzes the pixel patterns, recognizes characters,
         and returns a plain text string.

    PREPROCESSING (why we don't do it here):
      Professional OCR pipelines often pre-process images:
      - Convert to greyscale (removes color noise)
      - Increase contrast
      - Deskew (straighten tilted scans)
      We keep it simple for now. Greyscale conversion is done
      by the caller when beneficial.

    WHY ACCEPT A PIL IMAGE, NOT A FILE PATH?
      extract_text_from_scanned_pdf() converts PDF pages to PIL
      Images in memory — there's no file to pass. Accepting a PIL
      Image keeps the function reusable for both cases.

    Args:
        image: A PIL Image object (any mode — RGB, L, RGBA, etc.)

    Returns:
        Extracted text as a string. Empty string if no text found.

    Raises:
        RuntimeError: if Tesseract fails or is not installed.
    """
    _verify_tesseract()

    try:
        # Convert to greyscale — Tesseract works better on L (greyscale)
        # than RGB. Removing colour information reduces noise.
        grey_image = image.convert("L")

        # image_to_string returns a UTF-8 string.
        # config: --oem 3 = use LSTM + legacy engine (best accuracy)
        #         --psm 3 = fully automatic page segmentation (default)
        text = pytesseract.image_to_string(
            grey_image,
            lang=TESSERACT_LANG,
            config="--oem 3 --psm 3",
        )
        return text.strip()

    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract binary not found. Install with: brew install tesseract"
        )
    except Exception as e:
        raise RuntimeError(f"OCR failed on image: {e}")


# ─────────────────────────────────────────────────────────
# FUNCTION 3: extract_text_from_scanned_pdf()
# ─────────────────────────────────────────────────────────

def extract_text_from_scanned_pdf(file_path: str) -> dict:
    """
    Extract text from a scanned PDF by converting each page to
    an image and running OCR on it.

    HOW IT WORKS:
      Step 1: pdf2image.convert_from_path() calls the 'pdftoppm'
              tool (part of poppler) to render each PDF page as
              a high-resolution PIL Image (300 DPI).

      Step 2: For each page image, call extract_text_from_image()
              which runs Tesseract.

      Step 3: Collect all page texts, join with double newlines,
              count words, and return the result dict.

    WHY PROCESS ONE PAGE AT A TIME?
      A 100-page scanned PDF at 300 DPI → each page image is
      roughly 2500×3300 pixels at 8-bit greyscale ≈ 8 MB per page.
      Loading all 100 pages at once = ~800 MB RAM. Processing one
      page at a time keeps memory usage low and constant.

    WHY 300 DPI?
      Tesseract's accuracy drops significantly below 200 DPI.
      300 DPI is the sweet spot recommended by the Tesseract docs
      for document OCR.

    Args:
        file_path: Absolute path to a scanned .pdf file.

    Returns:
        dict: { documentType, ocrUsed, pageCount, wordCount,
                characterCount, language, text }

    Raises:
        ValueError: for corrupted, password-protected, or empty PDFs.
        RuntimeError: for missing poppler or Tesseract.
    """
    _verify_tesseract()

    # ── Check poppler is available ─────────────────────────
    # pdf2image internally calls 'pdftoppm' from the poppler package.
    if shutil.which("pdftoppm") is None:
        raise RuntimeError(
            "poppler is not installed (required for scanned PDF conversion). "
            "Install with: brew install poppler  (macOS) "
            "or: sudo apt install poppler-utils  (Linux)"
        )

    # ── Convert PDF pages to images ────────────────────────
    try:
        # convert_from_path renders all pages as PIL Images.
        # dpi=300 → high enough for accurate OCR.
        # thread_count=1 → deterministic, avoids race conditions.
        # We use a generator-like approach: fmt="jpeg" is smaller
        # than PNG, fast to decode, good enough quality for OCR.
        pages: list[Image.Image] = convert_from_path(
            file_path,
            dpi=PDF_DPI,
            thread_count=1,
            fmt="jpeg",
        )
    except Exception as e:
        error_msg = str(e).lower()
        if "password" in error_msg or "encrypted" in error_msg:
            raise ValueError(
                "This PDF is password-protected. "
                "Remove the password before uploading."
            )
        raise ValueError(f"Cannot convert PDF pages to images: {e}")

    if not pages:
        raise ValueError("PDF produced no renderable pages.")

    page_count = len(pages)
    page_texts: list[str] = []

    # ── OCR each page one at a time ────────────────────────
    for page_num, page_image in enumerate(pages, start=1):
        try:
            page_text = extract_text_from_image(page_image)
        except RuntimeError:
            # If OCR fails on one page (e.g. completely blank),
            # skip it rather than failing the whole document.
            page_text = ""

        if page_text:
            page_texts.append(page_text)

        # Free the image from memory immediately after OCR.
        # This keeps peak RAM usage at ~1 page at a time.
        page_image.close()

    full_text = "\n\n".join(page_texts)

    return {
        "documentType":   "pdf_scanned",
        "ocrUsed":        True,
        "pageCount":      page_count,
        "wordCount":      len(full_text.split()),
        "characterCount": len(full_text),
        "language":       "English",
        "text":           full_text,
    }


# ─────────────────────────────────────────────────────────
# FUNCTION 4: extract_text_from_searchable_pdf()
# ─────────────────────────────────────────────────────────

def extract_text_from_searchable_pdf(file_path: str) -> dict:
    """
    Extract text from a searchable PDF by reusing Module 2A's
    extract_pdf_text() — no OCR needed.

    WHY DOES THIS WRAPPER EXIST?
      Module 2A's extract_pdf_text() returns:
        { documentType, pageCount, wordCount, text }

      Module 2B's response needs extra fields:
        { documentType, ocrUsed, characterCount, language, ... }

      This function calls 2A's extractor and adds the missing
      fields — avoiding code duplication while adapting the shape.

    Args:
        file_path: Absolute path to a searchable .pdf file.

    Returns:
        dict with all OCR response fields, ocrUsed=False.

    Raises:
        ValueError: passed through from extract_pdf_text()
    """
    # Delegate all actual extraction to Module 2A
    result = extract_pdf_text(file_path)
    text = result["text"]

    return {
        "documentType":   "pdf_searchable",
        "ocrUsed":        False,          # No OCR — text was embedded
        "pageCount":      result["pageCount"],
        "wordCount":      result["wordCount"],
        "characterCount": len(text),
        "language":       "English",
        "text":           text,
    }


# ─────────────────────────────────────────────────────────
# FUNCTION 5: extract_text() — Master Dispatcher
# ─────────────────────────────────────────────────────────

def extract_text(file_path: str, file_extension: str) -> dict:
    """
    Master dispatcher — determines the correct extraction strategy
    based on file type and (for PDFs) content type.

    HOW IT WORKS:
      ┌──────────────┐
      │  file_path   │
      └──────┬───────┘
             │
      ┌──────▼───────────────────────────────────────┐
      │   extension is .jpg / .jpeg / .png?          │
      │   → load image → extract_text_from_image()   │
      └──────┬───────────────────────────────────────┘
             │ (extension is .pdf)
      ┌──────▼───────────────────────────────────────┐
      │   detect_pdf_type()                          │
      │   → "searchable"? → extract_text_from_       │
      │                      searchable_pdf()         │
      │   → "scanned"?    → extract_text_from_       │
      │                      scanned_pdf()            │
      └──────────────────────────────────────────────┘

    WHY IS THIS THE RIGHT DESIGN?
      The caller (router) should not need to know WHICH function
      to call — that's implementation detail. The router just says
      "here's a file, give me text". This function figures out how.
      This is the Strategy Pattern.

    Args:
        file_path:      Absolute path to the uploaded file on disk.
        file_extension: Lowercase file extension, e.g. ".pdf", ".jpg"

    Returns:
        dict with OCR response fields (ready to build OcrResponse)

    Raises:
        ValueError:  known bad input (wrong format, empty, password)
        RuntimeError: missing system tool or unexpected failure
    """
    ext = file_extension.lower()

    # ── Image files — run OCR directly ────────────────────
    if ext in (".jpg", ".jpeg", ".png"):
        # Open and validate the image FIRST — before checking Tesseract.
        # A corrupted file should raise ValueError immediately,
        # regardless of whether Tesseract is installed.
        try:
            image = Image.open(file_path)
        except Exception as e:
            raise ValueError(f"Cannot open image file: {e}")

        # verify() checks image data integrity (truncated / corrupt files).
        # It closes the image internally — we must re-open after.
        try:
            image.verify()
            image = Image.open(file_path)
        except Exception:
            raise ValueError(
                "The uploaded file appears to be corrupted or is not a valid image."
            )

        # Image is confirmed valid — now check Tesseract is present
        _verify_tesseract()

        text = extract_text_from_image(image)
        image.close()

        if not text:
            raise ValueError(
                "OCR produced no text. The image may be blank, "
                "too low resolution, or contain no readable text."
            )

        return {
            "documentType":   ext.lstrip("."),     # "jpg", "jpeg", or "png"
            "ocrUsed":        True,
            "pageCount":      1,                    # images are always 1 page
            "wordCount":      len(text.split()),
            "characterCount": len(text),
            "language":       "English",
            "text":           text,
        }

    # ── PDF — detect type first, then dispatch ─────────────
    elif ext == ".pdf":
        pdf_type = detect_pdf_type(file_path)

        if pdf_type == "searchable":
            return extract_text_from_searchable_pdf(file_path)
        else:
            return extract_text_from_scanned_pdf(file_path)

    # ── Unknown extension ──────────────────────────────────
    else:
        raise ValueError(
            f"Unsupported file extension '{ext}'. "
            "Supported: .pdf, .jpg, .jpeg, .png"
        )
