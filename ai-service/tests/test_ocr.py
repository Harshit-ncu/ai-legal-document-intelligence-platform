# tests/test_ocr.py
# ─────────────────────────────────────────────────────────
# Unit tests for Module 2B (OCR).
#
# TESTING STRATEGY:
#   We test the utility functions directly — no HTTP server
#   needed. This makes tests fast and isolated.
#
#   For tests that require Tesseract to be installed, we use
#   pytest.importorskip() or check for the binary first.
#   Tests that can run without Tesseract (error paths, PDF
#   detection, image loading) run unconditionally.
# ─────────────────────────────────────────────────────────

import os
import shutil
import tempfile
import pytest
from PIL import Image, ImageDraw, ImageFont

from app.utils.ocr_helpers import detect_pdf_type, extract_text

TESSERACT_AVAILABLE = shutil.which("tesseract") is not None
POPPLER_AVAILABLE   = shutil.which("pdftoppm") is not None


# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────

def make_white_image(width: int = 400, height: int = 100) -> Image.Image:
    """Create a blank white PIL Image."""
    return Image.new("RGB", (width, height), color=(255, 255, 255))


def make_text_image(text: str = "Hello World") -> Image.Image:
    """
    Create a PIL Image with black text on a white background.
    Uses the default bitmap font — no font file required.
    """
    img = Image.new("RGB", (500, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # load_default() uses a built-in tiny bitmap font
    font = ImageFont.load_default()
    draw.text((10, 30), text, fill=(0, 0, 0), font=font)
    return img


def make_txt_file(content: str) -> str:
    """Write content to a temp .txt file. Caller must delete."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        return f.name


def make_png_file(text: str = "Legal Contract") -> str:
    """Create a PNG file with text. Caller must delete."""
    img = make_text_image(text)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name
    img.save(path)
    return path


def make_blank_png_file() -> str:
    """Create a blank white PNG file."""
    img = make_white_image()
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name
    img.save(path)
    return path


# ─────────────────────────────────────────────────────────
# Test 1: detect_pdf_type — error on non-PDF
# ─────────────────────────────────────────────────────────

class TestDetectPdfType:
    def test_rejects_non_pdf_file(self):
        """A plain text file renamed to .pdf should raise ValueError."""
        path = make_txt_file("this is not a PDF")
        pdf_path = path.replace(".txt", "_fake.pdf")
        os.rename(path, pdf_path)
        try:
            with pytest.raises(ValueError, match="Cannot open PDF"):
                detect_pdf_type(pdf_path)
        finally:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)


# ─────────────────────────────────────────────────────────
# Test 2: Image loading
# ─────────────────────────────────────────────────────────

class TestImageHandling:
    def test_corrupted_image_raises_value_error(self):
        """A .png file with garbage bytes should raise ValueError."""
        path = make_txt_file("not an image at all !!!")
        png_path = path.replace(".txt", ".png")
        os.rename(path, png_path)
        try:
            with pytest.raises(ValueError):
                extract_text(png_path, ".png")
        finally:
            if os.path.exists(png_path):
                os.unlink(png_path)

    def test_unsupported_extension_raises_value_error(self):
        """Unsupported extension should raise ValueError."""
        path = make_txt_file("some content")
        try:
            with pytest.raises(ValueError, match="Unsupported file extension"):
                extract_text(path, ".bmp")
        finally:
            os.unlink(path)

    @pytest.mark.skipif(
        not TESSERACT_AVAILABLE,
        reason="Tesseract not installed — skipping live OCR test",
    )
    def test_blank_image_raises_value_error(self):
        """
        A completely blank white image should cause extract_text()
        to raise ValueError because OCR produces no text.
        """
        path = make_blank_png_file()
        try:
            with pytest.raises(ValueError, match="OCR produced no text"):
                extract_text(path, ".png")
        finally:
            os.unlink(path)

    @pytest.mark.skipif(
        not TESSERACT_AVAILABLE,
        reason="Tesseract not installed — skipping live OCR test",
    )
    def test_text_image_returns_text(self):
        """
        An image with actual printed text should return non-empty text.
        NOTE: Tesseract accuracy on tiny bitmap fonts varies.
        We only check that SOME text was extracted.
        """
        path = make_png_file("LEGAL CONTRACT 2024")
        try:
            result = extract_text(path, ".png")
            assert result["ocrUsed"] is True
            assert result["pageCount"] == 1
            assert result["documentType"] == "png"
            assert len(result["text"]) > 0
        finally:
            os.unlink(path)


# ─────────────────────────────────────────────────────────
# Test 3: Missing Tesseract
# ─────────────────────────────────────────────────────────

class TestMissingTesseract:
    @pytest.mark.skipif(
        TESSERACT_AVAILABLE,
        reason="Tesseract IS installed — this test only runs without it",
    )
    def test_missing_tesseract_raises_runtime_error(self):
        """When Tesseract is absent, a clear RuntimeError is raised."""
        path = make_png_file("hello")
        try:
            with pytest.raises(RuntimeError, match="Tesseract OCR is not installed"):
                extract_text(path, ".png")
        finally:
            os.unlink(path)


# ─────────────────────────────────────────────────────────
# HOW TO RUN THESE TESTS
# ─────────────────────────────────────────────────────────
# From ai-service/ directory:
#
#   source .venv/bin/activate
#   python -m pytest tests/test_ocr.py -v
#
# To run only tests that don't need Tesseract:
#   python -m pytest tests/test_ocr.py -v -k "not live"
#
# To run ALL tests including OCR (needs Tesseract installed):
#   python -m pytest tests/ -v
