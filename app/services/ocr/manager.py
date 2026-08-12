"""
Legal AI System - OCR Manager
=================================
Central manager that orchestrates the full OCR pipeline:
1. Detect if a document needs OCR
2. Convert PDFs to images if needed
3. Run OCR via the configured provider
4. Cleanup temp files

This is the single entry point that the AI service calls.
"""

import os
import logging
from typing import Optional

from app.services.ocr.base import OCRProvider
from app.services.ocr.easyocr_provider import EasyOCRProvider
from app.services.ocr.detector import is_scanned_pdf, convert_pdf_to_images, cleanup_temp_images

logger = logging.getLogger(__name__)


# Image file extensions that should go directly to OCR
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}


class OCRManager:
    """
    Orchestrates the OCR pipeline.
    
    - Automatically detects whether a PDF is scanned or native.
    - Routes scanned PDFs and images through the configured OCR provider.
    - Falls back gracefully if OCR fails.
    
    Usage:
        from app.services.ocr import ocr_manager
        text = ocr_manager.extract_text("path/to/document.pdf")
    """

    def __init__(self, provider: Optional[OCRProvider] = None):
        """
        Initialize the OCR Manager.
        
        Args:
            provider: An OCR provider instance. Defaults to EasyOCR.
                      Swap this to GoogleVisionProvider or TesseractProvider later.
        """
        self._provider = provider  # Lazy-loaded if None

    def _get_provider(self) -> OCRProvider:
        """Lazy-load the OCR provider to avoid loading heavy models at startup."""
        if self._provider is None:
            logger.info("Initializing default OCR provider: EasyOCR")
            self._provider = EasyOCRProvider(languages=['en'])
        return self._provider

    def extract_text(self, file_path: str) -> str:
        """
        Smart text extraction from any document type.
        
        Decision flow:
        1. If file is an image (JPG/PNG) → directly run OCR.
        2. If file is a PDF:
           a. Try pdfplumber for native text.
           b. If no text found (scanned) → convert to images → run OCR.
        3. If file is DOCX → use python-docx.
        4. Fallback → read as plain text.
        
        Args:
            file_path: Absolute path to the document.
            
        Returns:
            Extracted text string (max 30,000 characters).
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return ""

        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        text = ""

        try:
            # --- Image files → Direct OCR ---
            if ext in IMAGE_EXTENSIONS:
                logger.info(f"Image file detected ({ext}). Running OCR directly.")
                provider = self._get_provider()
                text = provider.extract_text_from_image(file_path)

            # --- PDF files → Smart detection ---
            elif ext == '.pdf':
                text = self._extract_from_pdf(file_path)

            # --- DOCX files → python-docx ---
            elif ext == '.docx':
                text = self._extract_from_docx(file_path)

            # --- Fallback → plain text ---
            else:
                logger.info(f"Unknown extension ({ext}). Attempting plain text read.")
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()

        except Exception as e:
            logger.error(f"Text extraction failed for {file_path}: {e}", exc_info=True)

        # Cap at 30,000 characters to avoid exceeding AI context windows
        return text[:30000]

    def _extract_from_pdf(self, file_path: str) -> str:
        """
        Extract text from a PDF with smart scanned-document detection.
        
        1. Try pdfplumber first (fast, native text).
        2. If no text found, check if it's a scanned PDF.
        3. If scanned, convert to images and run OCR.
        """
        import pdfplumber

        # Step 1: Try native text extraction
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.warning(f"pdfplumber failed on {file_path}: {e}")

        # If we got meaningful text, return it
        if text.strip() and len(text.strip()) > 50:
            logger.info(f"Native text extracted from PDF ({len(text)} chars). No OCR needed.")
            return text

        # Step 2: PDF is likely scanned — verify and run OCR
        logger.info(f"No native text in PDF. Checking if scanned...")
        
        if is_scanned_pdf(file_path):
            logger.info(f"Confirmed scanned PDF. Converting to images for OCR...")
            image_paths = convert_pdf_to_images(file_path)
            
            if image_paths:
                try:
                    provider = self._get_provider()
                    text = provider.extract_text_from_images(image_paths)
                    logger.info(f"OCR extracted {len(text)} characters from {len(image_paths)} pages.")
                finally:
                    # Always cleanup temp images
                    cleanup_temp_images(image_paths)
            else:
                logger.warning("PDF-to-image conversion produced no images. OCR skipped.")
        else:
            logger.info("PDF has some text but below threshold. Returning what was found.")

        return text

    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from a DOCX file using python-docx."""
        try:
            import docx
            doc = docx.Document(file_path)
            text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
            logger.info(f"Extracted {len(text)} characters from DOCX.")
            return text
        except Exception as e:
            logger.error(f"DOCX extraction failed: {e}")
            return ""


# Singleton instance — import this across the application
ocr_manager = OCRManager()
