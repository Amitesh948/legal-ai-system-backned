"""
Legal AI System - OCR Base Provider
======================================
Abstract base class for OCR providers.
All OCR implementations must inherit from this class,
making the OCR engine swappable (EasyOCR → Google Vision → AWS Textract).
"""

import logging
from abc import ABC, abstractmethod
from typing import List

logger = logging.getLogger(__name__)


class OCRProvider(ABC):
    """
    Abstract base class for OCR providers.
    
    Any new OCR engine (Google Vision, AWS Textract, Tesseract)
    can be plugged in by implementing this interface.
    """

    @abstractmethod
    def extract_text_from_image(self, image_path: str) -> str:
        """
        Extract text from a single image file (JPG, PNG, etc.).
        
        Args:
            image_path: Absolute path to the image file.
            
        Returns:
            Extracted text as a single string.
        """
        pass

    @abstractmethod
    def extract_text_from_images(self, image_paths: List[str]) -> str:
        """
        Extract text from multiple image files and concatenate results.
        
        Args:
            image_paths: List of absolute paths to image files.
            
        Returns:
            Combined extracted text from all images.
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the name of the OCR provider for logging."""
        pass
