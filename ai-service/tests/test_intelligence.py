# tests/test_intelligence.py
# ─────────────────────────────────────────────────────────
# Unit tests for Feature 4 (Document Intelligence)
# ─────────────────────────────────────────────────────────

import os
import tempfile
import pytest
from PIL import Image, ImageDraw

from app.utils.intelligence import (
    clean_text,
    calculate_document_statistics,
    detect_language,
    classify_document
)
from app.services.intelligence import analyze_document


# ── 1. Unit Tests for Intelligence Utilities ──────────────

class TestCleanText:
    def test_normalizes_newlines(self):
        text = "Line 1\r\nLine 2"
        assert clean_text(text) == "Line 1\nLine 2"

    def test_collapses_multiple_newlines(self):
        text = "Paragraph 1\n\n\n\n\nParagraph 2"
        assert clean_text(text) == "Paragraph 1\n\nParagraph 2"

    def test_collapses_multiple_spaces(self):
        text = "Word    and   another\tword"
        assert clean_text(text) == "Word and another word"

    def test_strips_whitespace(self):
        text = "  \n  Hello World  \n  "
        assert clean_text(text) == "Hello World"


class TestCalculateDocumentStatistics:
    def test_basic_stats(self):
        text = "This is a sentence. This is another sentence!\n\nNew paragraph."
        stats = calculate_document_statistics(text)
        assert stats["wordCount"] == 10
        assert stats["characterCount"] == len(text)
        assert stats["paragraphCount"] == 2
        assert stats["sentenceCount"] == 3
        # 10 words at 238 wpm is <1 min, rounded to 1
        assert stats["estimatedReadingTimeMinutes"] == 1

    def test_empty_text(self):
        stats = calculate_document_statistics("")
        assert stats["wordCount"] == 0
        assert stats["paragraphCount"] == 0
        assert stats["estimatedReadingTimeMinutes"] == 0


class TestDetectLanguage:
    def test_detect_english(self):
        text = "This is a standard English contract regarding confidentiality."
        lang, conf = detect_language(text)
        assert lang == "English"
        assert conf > 0.9

    def test_detect_spanish(self):
        text = "Este es un contrato de confidencialidad estándar."
        lang, conf = detect_language(text)
        assert lang == "Spanish"

    def test_unknown_or_gibberish(self):
        text = "12345 67890 !@#$%"
        lang, conf = detect_language(text)
        assert lang == "Unknown"
        assert conf == 0.0


class TestClassifyDocument:
    def test_nda(self):
        text = "This non-disclosure agreement is between the disclosing party and receiving party."
        doc_type, conf = classify_document(text)
        assert doc_type == "NDA"
        assert conf > 0.0

    def test_lease(self):
        text = "The tenant agrees to pay rent to the landlord for the premises."
        doc_type, conf = classify_document(text)
        assert doc_type == "Lease Agreement"
        assert conf > 0.0

    def test_unknown(self):
        text = "Just some random text about cooking recipes."
        doc_type, conf = classify_document(text)
        assert doc_type == "Unknown"
        assert conf == 0.0


# ── 2. Integration Tests for analyze_document ─────────────

def make_temp_file(content: str, ext: str) -> str:
    with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False, encoding="utf-8") as f:
        f.write(content)
        return f.name

def make_temp_image(text: str) -> str:
    img = Image.new("RGB", (500, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((10, 30), text, fill=(0, 0, 0))
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name
    img.save(path)
    return path

class TestAnalyzeDocument:
    def test_txt_file_integration(self):
        content = "This non-disclosure agreement is strictly confidential.\n\nThe receiving party agrees."
        path = make_temp_file(content, ".txt")
        try:
            result = analyze_document(path, ".txt", "test.txt")
            assert result["documentType"] == "txt"
            assert result["ocrUsed"] is False
            assert result["classification"] == "NDA"
            assert result["language"] == "English"
            assert result["wordCount"] == 10
        finally:
            os.unlink(path)

    def test_image_file_integration(self):
        # Requires Tesseract
        import shutil
        if not shutil.which("tesseract"):
            pytest.skip("Tesseract not installed")
            
        path = make_temp_image("non-disclosure agreement")
        try:
            result = analyze_document(path, ".png", "test.png")
            assert result["documentType"] == "png"
            assert result["ocrUsed"] is True
            assert result["classification"] == "NDA"
        finally:
            os.unlink(path)

    def test_unsupported_file(self):
        path = make_temp_file("fake", ".mp4")
        try:
            with pytest.raises(ValueError, match="Unsupported file extension"):
                analyze_document(path, ".mp4", "test.mp4")
        finally:
            os.unlink(path)
