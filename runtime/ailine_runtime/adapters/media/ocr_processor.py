"""OCR processor for extracting text from PDFs and images.

Uses pypdf for native PDF text extraction and pytesseract for
image-based OCR.  Both are lazy-imported so the module can be
loaded even when the underlying libraries are not installed
(ADR-041).

Requires:
- ``pypdf>=5`` for PDF text extraction.
- ``pytesseract>=0.3`` + system Tesseract binary for image OCR.
"""

from __future__ import annotations

import asyncio
import io

import structlog

logger = structlog.get_logger(__name__)

# Supported file types for the public API
PDF_TYPE = "pdf"
IMAGE_TYPE = "image"


class OCRProcessor:
    """Extract text from PDF/image files.

    This is a utility adapter -- it does not map to a single port
    protocol but is used by application-layer services that need
    document text extraction (material ingestion, accessibility
    features).
    """

    async def extract_text(
        self, file_bytes: bytes, *, file_type: str = PDF_TYPE
    ) -> str:
        """Extract text from the given file bytes.

        Parameters
        ----------
        file_bytes:
            Raw file content.
        file_type:
            ``"pdf"`` or ``"image"``.

        Returns
        -------
        str
            Extracted text, or a diagnostic message if the required
            library is not available.
        """
        loop = asyncio.get_running_loop()
        if file_type == PDF_TYPE:
            return await loop.run_in_executor(None, self._extract_pdf, file_bytes)
        return await loop.run_in_executor(None, self._extract_image, file_bytes)

    # -- Private sync helpers (run in executor) ----------------------------

    def _extract_pdf(self, file_bytes: bytes) -> str:
        """Extract text from a PDF using pypdf."""
        try:
            from pypdf import PdfReader
        except ImportError:
            logger.warning("ocr.pypdf_missing")
            return "[Extracao de texto PDF requer pypdf instalado]"

        reader = PdfReader(io.BytesIO(file_bytes))
        pages: list[str] = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n".join(pages)

    def _extract_image(self, file_bytes: bytes) -> str:
        """Extract text from an image using pytesseract + Pillow."""
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            logger.warning("ocr.pytesseract_missing")
            return "[OCR de imagem requer pytesseract e Pillow instalados]"

        try:
            image = Image.open(io.BytesIO(file_bytes))
            text: str = pytesseract.image_to_string(image, lang="por+eng")
            return text.strip()
        except OSError:
            logger.exception("ocr.image_extraction_failed")
            return "[Falha na extracao de texto da imagem]"
