"""
Legal AI System - EasyOCR Provider
=====================================
Concrete OCR implementation using EasyOCR.
EasyOCR is a free, open-source OCR library that supports 80+ languages.
No API key or external service required — runs entirely on CPU/GPU locally.
"""

import logging
from typing import List

from app.services.ocr.base import OCRProvider

logger = logging.getLogger(__name__)


class EasyOCRProvider(OCRProvider):
    """
    OCR provider using EasyOCR library.
    
    - Supports 80+ languages (default: English)
    - Runs locally (no API keys needed)
    - GPU accelerated when available, falls back to CPU
    """

    def __init__(self, languages: List[str] = None):
        """
        Initialize EasyOCR reader.
        
        Args:
            languages: List of language codes (e.g., ['en', 'hi'] for English + Hindi).
                       Defaults to English only.
        """
        self._reader = None
        self._languages = languages or ['en']

    def _get_reader(self):
        """Lazy-load the EasyOCR reader to avoid slow startup times."""
        if self._reader is None:
            try:
                import easyocr
                logger.info(f"Initializing EasyOCR reader for languages: {self._languages}")
                self._reader = easyocr.Reader(self._languages, gpu=False)
                logger.info("EasyOCR reader initialized successfully.")
            except ImportError:
                logger.error("EasyOCR is not installed. Run: pip install easyocr")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR: {e}")
                raise
        return self._reader

    def extract_text_from_image(self, image_path: str) -> str:
        """
        Extract text from a single image file.
        
        Args:
            image_path: Absolute path to JPG, PNG, or other image file.
            
        Returns:
            Extracted text as a single string.
        """
        try:
            reader = self._get_reader()
            results = reader.readtext(image_path, detail=0)  # detail=0 returns only text strings
            extracted = "\n".join(results)
            logger.info(f"EasyOCR extracted {len(extracted)} characters from {image_path}")
            return extracted
        except Exception as e:
            logger.error(f"EasyOCR failed to process {image_path}: {e}")
            return ""

    def extract_text_from_images(self, image_paths: List[str]) -> str:
        """
        Extract text from multiple image files and concatenate results.
        
        Args:
            image_paths: List of absolute paths to image files.
            
        Returns:
            Combined text from all images, separated by page markers.
        """
        all_text = []
        for i, path in enumerate(image_paths):
            page_text = self.extract_text_from_image(path)
            if page_text.strip():
                all_text.append(f"--- Page {i + 1} ---\n{page_text}")
            else:
                all_text.append(f"--- Page {i + 1} ---\n[No text detected]")
        
        return "\n\n".join(all_text)

    def get_provider_name(self) -> str:
        return "EasyOCR"
