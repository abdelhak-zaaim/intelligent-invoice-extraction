"""OCR interface and implementations for text extraction from invoices."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class OCREngine(ABC):
    """Abstract base class for OCR engines."""
    
    @abstractmethod
    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text from an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        pass
    
    @abstractmethod
    def preprocess_image(self, image_path: str) -> Any:
        """
        Preprocess image for better OCR results.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Preprocessed image
        """
        pass


class TesseractOCR(OCREngine):
    """Tesseract OCR implementation."""
    
    def __init__(self, language: str = "eng", dpi: int = 300, preprocessing: bool = True):
        """
        Initialize Tesseract OCR engine.
        
        Args:
            language: OCR language (default: eng)
            dpi: DPI for image processing
            preprocessing: Enable image preprocessing
        """
        self.language = language
        self.dpi = dpi
        self.preprocessing = preprocessing
        self._libraries_loaded = False
        
        try:
            import pytesseract
            from PIL import Image
            import cv2
            import numpy as np
            self.pytesseract = pytesseract
            self.Image = Image
            self.cv2 = cv2
            self.np = np
            self._libraries_loaded = True
        except ImportError as e:
            logger.warning(f"OCR libraries not installed: {e}. Install with: pip install pytesseract Pillow opencv-python")
            # Don't raise - allow graceful degradation
    
    def preprocess_image(self, image_path: str) -> Any:
        """
        Preprocess image for better OCR results.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Preprocessed image
        """
        if not self._libraries_loaded:
            raise RuntimeError("OCR libraries not installed. Install with: pip install pytesseract Pillow opencv-python")
        
        if not self.preprocessing:
            return self.Image.open(image_path)
        
        # Read image
        img = self.cv2.imread(image_path)
        
        # Convert to grayscale
        gray = self.cv2.cvtColor(img, self.cv2.COLOR_BGR2GRAY)
        
        # Apply denoising
        denoised = self.cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Apply thresholding
        _, thresh = self.cv2.threshold(denoised, 0, 255, self.cv2.THRESH_BINARY + self.cv2.THRESH_OTSU)
        
        return self.Image.fromarray(thresh)
    
    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text from an image using Tesseract.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        if not self._libraries_loaded:
            return {
                'text': '',
                'raw_data': {},
                'success': False,
                'error': 'OCR libraries not installed. Install with: pip install pytesseract Pillow opencv-python',
                'engine': 'tesseract'
            }
        
        try:
            # Preprocess image
            image = self.preprocess_image(image_path)
            
            # Extract text
            text = self.pytesseract.image_to_string(image, lang=self.language)
            
            # Extract detailed data with bounding boxes
            data = self.pytesseract.image_to_data(image, lang=self.language, output_type=self.pytesseract.Output.DICT)
            
            return {
                'text': text,
                'raw_data': data,
                'success': True,
                'engine': 'tesseract'
            }
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return {
                'text': '',
                'raw_data': {},
                'success': False,
                'error': str(e),
                'engine': 'tesseract'
            }


class PDFOCREngine(OCREngine):
    """OCR engine for PDF documents."""
    
    def __init__(self, ocr_engine: OCREngine, dpi: int = 300):
        """
        Initialize PDF OCR engine.
        
        Args:
            ocr_engine: Underlying OCR engine to use
            dpi: DPI for PDF to image conversion
        """
        self.ocr_engine = ocr_engine
        self.dpi = dpi
        
        try:
            from pdf2image import convert_from_path
            self.convert_from_path = convert_from_path
        except ImportError as e:
            logger.error(f"Failed to import pdf2image: {e}")
            raise
    
    def preprocess_image(self, image_path: str) -> Any:
        """Use underlying OCR engine's preprocessing."""
        return self.ocr_engine.preprocess_image(image_path)
    
    def extract_text(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text from a PDF document.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            # Convert PDF to images
            images = self.convert_from_path(pdf_path, dpi=self.dpi)
            
            all_text = []
            all_data = []
            
            # Process each page
            for i, image in enumerate(images):
                # Save temporary image
                temp_path = f"/tmp/page_{i}.png"
                image.save(temp_path, 'PNG')
                
                # Extract text from image
                result = self.ocr_engine.extract_text(temp_path)
                
                if result['success']:
                    all_text.append(f"--- Page {i+1} ---\n{result['text']}")
                    all_data.append({
                        'page': i + 1,
                        'data': result['raw_data']
                    })
            
            return {
                'text': '\n\n'.join(all_text),
                'raw_data': all_data,
                'success': True,
                'pages': len(images),
                'engine': f'pdf_{self.ocr_engine.__class__.__name__}'
            }
        except Exception as e:
            logger.error(f"PDF OCR extraction failed: {e}")
            return {
                'text': '',
                'raw_data': [],
                'success': False,
                'error': str(e),
                'engine': 'pdf_ocr'
            }


def create_ocr_engine(engine_type: str = "tesseract", **kwargs) -> OCREngine:
    """
    Factory function to create OCR engine.
    
    Args:
        engine_type: Type of OCR engine (tesseract, pdf)
        **kwargs: Additional arguments for the OCR engine
        
    Returns:
        OCR engine instance
    """
    if engine_type == "tesseract":
        return TesseractOCR(**kwargs)
    elif engine_type == "pdf":
        base_engine = TesseractOCR(**kwargs)
        return PDFOCREngine(base_engine, dpi=kwargs.get('dpi', 300))
    else:
        raise ValueError(f"Unknown OCR engine type: {engine_type}")
