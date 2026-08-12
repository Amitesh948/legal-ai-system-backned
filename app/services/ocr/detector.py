"""
Legal AI System - Scanned Document Detector
===============================================
Detects whether a PDF contains selectable (native) text or is a scanned image.
This avoids unnecessarily running expensive OCR on PDFs that already have text.
"""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def is_scanned_pdf(file_path: str, sample_pages: int = 3) -> bool:
    """
    Detect whether a PDF is scanned (image-only) or contains native selectable text.
    
    Strategy:
    - Open the first N pages with pdfplumber.
    - If extractable text is found → it's a native PDF (no OCR needed).
    - If no text is found on any page → it's likely a scanned document (OCR needed).
    
    Args:
        file_path: Absolute path to the PDF file.
        sample_pages: Number of pages to sample (default: first 3 pages).
        
    Returns:
        True if the PDF appears to be scanned (needs OCR), False if native text exists.
    """
    try:
        import pdfplumber
        
        with pdfplumber.open(file_path) as pdf:
            pages_to_check = min(len(pdf.pages), sample_pages)
            
            for i in range(pages_to_check):
                page = pdf.pages[i]
                text = page.extract_text()
                
                # If any page has meaningful text (more than just whitespace/headers),
                # treat the entire PDF as a native text PDF.
                if text and len(text.strip()) > 50:
                    logger.info(f"PDF has native text on page {i + 1}. OCR not needed.")
                    return False
            
            # No meaningful text found on any sampled page
            logger.info(f"PDF appears to be scanned (no text on first {pages_to_check} pages). OCR needed.")
            return True
            
    except Exception as e:
        logger.warning(f"Could not analyze PDF {file_path}: {e}. Assuming scanned.")
        return True


def convert_pdf_to_images(file_path: str, output_dir: str = None) -> list:
    """
    Convert each page of a PDF into individual image files for OCR processing.
    
    Uses PyPDF2 for page count, and pdf2image (poppler) for rendering.
    Falls back to a simpler approach if pdf2image is not available.
    
    Args:
        file_path: Absolute path to the PDF file.
        output_dir: Directory to save extracted images. Defaults to a temp directory.
        
    Returns:
        List of absolute paths to the generated image files.
    """
    import os
    import tempfile
    
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="ocr_pages_")
    
    os.makedirs(output_dir, exist_ok=True)
    image_paths = []
    
    try:
        # Try pdf2image first (requires poppler-utils system package)
        from pdf2image import convert_from_path
        
        logger.info(f"Converting PDF to images using pdf2image: {file_path}")
        images = convert_from_path(file_path, dpi=300, fmt='png')
        
        for i, image in enumerate(images):
            img_path = os.path.join(output_dir, f"page_{i + 1}.png")
            image.save(img_path, 'PNG')
            image_paths.append(img_path)
            
        logger.info(f"Converted {len(image_paths)} PDF pages to images.")
        
    except ImportError:
        logger.warning("pdf2image not installed. Falling back to PyPDF2 image extraction.")
        
        # Fallback: Extract embedded images from PDF using PyPDF2
        try:
            from PyPDF2 import PdfReader
            from PIL import Image
            import io
            
            reader = PdfReader(file_path)
            img_count = 0
            
            for page_num, page in enumerate(reader.pages):
                if '/XObject' in page['/Resources']:
                    x_objects = page['/Resources']['/XObject'].get_object()
                    for obj_name in x_objects:
                        obj = x_objects[obj_name].get_object()
                        if obj['/Subtype'] == '/Image':
                            try:
                                data = obj.get_data()
                                img = Image.open(io.BytesIO(data))
                                img_path = os.path.join(output_dir, f"page_{img_count + 1}.png")
                                img.save(img_path, 'PNG')
                                image_paths.append(img_path)
                                img_count += 1
                            except Exception:
                                continue
                                
            logger.info(f"Extracted {len(image_paths)} images from PDF using PyPDF2.")
            
        except Exception as e:
            logger.error(f"Failed to extract images from PDF: {e}")
    
    except Exception as e:
        logger.error(f"Failed to convert PDF to images: {e}")
    
    return image_paths


def cleanup_temp_images(image_paths: list):
    """Remove temporary image files created during OCR processing."""
    import os
    import shutil
    
    for path in image_paths:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
    
    # Also try to remove the parent temp directory if it's empty
    if image_paths:
        parent_dir = os.path.dirname(image_paths[0])
        try:
            if parent_dir and os.path.exists(parent_dir) and not os.listdir(parent_dir):
                shutil.rmtree(parent_dir, ignore_errors=True)
        except Exception:
            pass
