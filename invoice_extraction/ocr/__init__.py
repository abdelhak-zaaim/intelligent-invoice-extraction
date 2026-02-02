"""OCR module for text extraction."""

from .ocr_engine import OCREngine, TesseractOCR, PDFOCREngine, create_ocr_engine

__all__ = ["OCREngine", "TesseractOCR", "PDFOCREngine", "create_ocr_engine"]
