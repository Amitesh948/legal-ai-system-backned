"""
Legal AI System - OCR Module
===============================
Pluggable OCR abstraction layer.
Supports multiple providers (EasyOCR, Google Vision, etc.)
"""
from app.services.ocr.manager import ocr_manager

__all__ = ["ocr_manager"]
