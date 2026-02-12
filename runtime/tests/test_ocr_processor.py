"""Tests for OCR processor -- mocks pypdf and pytesseract."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ailine_runtime.adapters.media.ocr_processor import OCRProcessor


@pytest.fixture
def ocr():
    return OCRProcessor()


class TestExtractPdf:
    @pytest.mark.asyncio
    async def test_pdf_extraction(self, ocr):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Page one text"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        mock_pypdf = MagicMock()
        mock_pypdf.PdfReader.return_value = mock_reader

        with patch.dict("sys.modules", {"pypdf": mock_pypdf}):
            result = await ocr.extract_text(b"fake pdf bytes", file_type="pdf")
            assert result == "Page one text"

    @pytest.mark.asyncio
    async def test_pdf_multiple_pages(self, ocr):
        pages = []
        for text in ["Page 1", "Page 2", "Page 3"]:
            page = MagicMock()
            page.extract_text.return_value = text
            pages.append(page)

        mock_reader = MagicMock()
        mock_reader.pages = pages

        mock_pypdf = MagicMock()
        mock_pypdf.PdfReader.return_value = mock_reader

        with patch.dict("sys.modules", {"pypdf": mock_pypdf}):
            result = await ocr.extract_text(b"pdf", file_type="pdf")
            assert "Page 1" in result
            assert "Page 2" in result
            assert "Page 3" in result

    @pytest.mark.asyncio
    async def test_pdf_empty_page(self, ocr):
        page1 = MagicMock()
        page1.extract_text.return_value = "Good page"
        page2 = MagicMock()
        page2.extract_text.return_value = None  # Empty page

        mock_reader = MagicMock()
        mock_reader.pages = [page1, page2]

        mock_pypdf = MagicMock()
        mock_pypdf.PdfReader.return_value = mock_reader

        with patch.dict("sys.modules", {"pypdf": mock_pypdf}):
            result = await ocr.extract_text(b"pdf", file_type="pdf")
            assert result == "Good page"

    @pytest.mark.asyncio
    async def test_pdf_missing_library(self, ocr):
        with patch.dict("sys.modules", {"pypdf": None}):
            result = await ocr.extract_text(b"pdf", file_type="pdf")
            assert "pypdf" in result.lower() or "requer" in result.lower()


class TestExtractImage:
    @pytest.mark.asyncio
    async def test_image_extraction(self, ocr):
        mock_image = MagicMock()
        mock_pil = MagicMock()
        mock_pil.Image.open.return_value = mock_image

        mock_pytesseract = MagicMock()
        mock_pytesseract.image_to_string.return_value = "Extracted image text\n"

        with patch.dict(
            "sys.modules",
            {"pytesseract": mock_pytesseract, "PIL": mock_pil, "PIL.Image": mock_pil.Image},
        ):
            result = await ocr.extract_text(b"image bytes", file_type="image")
            assert result == "Extracted image text"

    @pytest.mark.asyncio
    async def test_image_missing_library(self, ocr):
        with patch.dict("sys.modules", {"pytesseract": None, "PIL": None, "PIL.Image": None}):
            result = await ocr.extract_text(b"image", file_type="image")
            assert "pytesseract" in result.lower() or "requer" in result.lower()

    @pytest.mark.asyncio
    async def test_image_extraction_failure(self, ocr):
        mock_pil = MagicMock()
        mock_pil.Image.open.side_effect = Exception("Bad image")
        mock_pytesseract = MagicMock()

        with patch.dict(
            "sys.modules",
            {"pytesseract": mock_pytesseract, "PIL": mock_pil, "PIL.Image": mock_pil.Image},
        ):
            result = await ocr.extract_text(b"bad image", file_type="image")
            assert "falha" in result.lower() or "image" in result.lower()
