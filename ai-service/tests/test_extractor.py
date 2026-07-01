# tests/test_extractor.py
# ─────────────────────────────────────────────────────────
# Unit tests for the text extraction service.
# Run with: pytest tests/ -v
#
# These tests call the service functions directly — no HTTP,
# no running server. This is fast and reliable.
# ─────────────────────────────────────────────────────────

import os
import tempfile
import pytest

from app.services.extractor import (
    extract_pdf_text,
    extract_docx_text,
    extract_txt_text,
    _count_words,
)


# ── Helper: create a real temp .txt file ──────────────────

def make_txt_file(content: str) -> str:
    """Write content to a temp file and return its path."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        return f.name


# ── _count_words ──────────────────────────────────────────

class TestCountWords:
    def test_normal_sentence(self):
        assert _count_words("The quick brown fox") == 4

    def test_extra_whitespace(self):
        assert _count_words("  hello   world  ") == 2

    def test_newlines(self):
        assert _count_words("line one\nline two\nline three") == 6

    def test_empty_string(self):
        assert _count_words("") == 0


# ── extract_txt_text ──────────────────────────────────────

class TestExtractTxtText:
    def test_basic_extraction(self):
        path = make_txt_file("This is a legal contract.\nSigned by both parties.")
        try:
            result = extract_txt_text(path)
            assert result["documentType"] == "txt"
            assert result["wordCount"] > 0
            assert "legal contract" in result["text"]
            assert result["pageCount"] == 2  # 2 non-empty lines
        finally:
            os.unlink(path)

    def test_word_count(self):
        path = make_txt_file("one two three four five")
        try:
            result = extract_txt_text(path)
            assert result["wordCount"] == 5
        finally:
            os.unlink(path)

    def test_empty_file(self):
        path = make_txt_file("")
        try:
            result = extract_txt_text(path)
            assert result["text"] == ""
            assert result["wordCount"] == 0
            assert result["pageCount"] == 0
        finally:
            os.unlink(path)

    def test_file_not_found(self):
        with pytest.raises(ValueError, match="File not found"):
            extract_txt_text("/tmp/does_not_exist_at_all.txt")

    def test_collapses_excess_blank_lines(self):
        path = make_txt_file("section one\n\n\n\nsection two")
        try:
            result = extract_txt_text(path)
            # Should not have more than 2 consecutive newlines
            assert "\n\n\n" not in result["text"]
        finally:
            os.unlink(path)


# ── extract_pdf_text ──────────────────────────────────────
# NOTE: Creating a valid PDF programmatically requires reportlab or
# fpdf2. For now we test the error path (bad file) and note that
# full PDF tests should use a fixture file in tests/fixtures/.

class TestExtractPdfText:
    def test_invalid_file_raises_value_error(self):
        path = make_txt_file("this is not a real pdf")
        try:
            # Rename to .pdf so the extractor attempts to parse it
            pdf_path = path.replace(".txt", "_fake.pdf")
            os.rename(path, pdf_path)
            with pytest.raises(ValueError, match="Cannot open PDF"):
                extract_pdf_text(pdf_path)
        finally:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)


# ── extract_docx_text ─────────────────────────────────────

class TestExtractDocxText:
    def test_invalid_file_raises_value_error(self):
        path = make_txt_file("this is not a real docx file")
        try:
            docx_path = path.replace(".txt", "_fake.docx")
            os.rename(path, docx_path)
            with pytest.raises(ValueError, match="Cannot open DOCX"):
                extract_docx_text(docx_path)
        finally:
            if os.path.exists(docx_path):
                os.unlink(docx_path)
