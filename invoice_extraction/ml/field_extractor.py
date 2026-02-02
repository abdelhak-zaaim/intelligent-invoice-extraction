"""Machine learning module for invoice field extraction."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Extraction constants
DEFAULT_CONFIDENCE_SCORE = 0.8  # Default confidence for pattern-based extraction


class FieldExtractor(ABC):
    """Abstract base class for field extraction."""
    
    @abstractmethod
    def extract_fields(self, text: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract invoice fields from text.
        
        Args:
            text: Extracted text from OCR
            raw_data: Raw OCR data with bounding boxes
            
        Returns:
            Dictionary containing extracted fields
        """
        pass


class PatternBasedExtractor(FieldExtractor):
    """Pattern-based field extraction using regex."""
    
    def __init__(self, confidence_threshold: float = 0.7):
        """
        Initialize pattern-based extractor.
        
        Args:
            confidence_threshold: Minimum confidence for field extraction
        """
        self.confidence_threshold = confidence_threshold
        
        # Define patterns for various fields
        self.patterns = {
            'invoice_number': [
                r'invoice\s*#?\s*:?\s*([A-Z0-9-]+)',
                r'inv\s*#?\s*:?\s*([A-Z0-9-]+)',
                r'invoice\s+number\s*:?\s*([A-Z0-9-]+)',
            ],
            'invoice_date': [
                r'date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'invoice\s+date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})',
            ],
            'supplier': [
                r'from\s*:?\s*([A-Za-z\s&.,]+?)(?:\n|$)',
                r'vendor\s*:?\s*([A-Za-z\s&.,]+?)(?:\n|$)',
                r'supplier\s*:?\s*([A-Za-z\s&.,]+?)(?:\n|$)',
            ],
            'total': [
                r'total\s*:?\s*\$?\s*([\d,]+\.?\d*)',
                r'amount\s+due\s*:?\s*\$?\s*([\d,]+\.?\d*)',
                r'grand\s+total\s*:?\s*\$?\s*([\d,]+\.?\d*)',
            ],
            'vat': [
                r'vat\s*:?\s*\$?\s*([\d,]+\.?\d*)',
                r'tax\s*:?\s*\$?\s*([\d,]+\.?\d*)',
                r'sales\s+tax\s*:?\s*\$?\s*([\d,]+\.?\d*)',
            ],
            'subtotal': [
                r'subtotal\s*:?\s*\$?\s*([\d,]+\.?\d*)',
                r'sub-total\s*:?\s*\$?\s*([\d,]+\.?\d*)',
            ],
        }
    
    def _extract_with_pattern(self, text: str, patterns: List[str]) -> Optional[str]:
        """
        Extract field using multiple patterns.
        
        Args:
            text: Text to search
            patterns: List of regex patterns
            
        Returns:
            Extracted value or None
        """
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_line_items(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract line items from invoice.
        
        Args:
            text: Invoice text
            
        Returns:
            List of line items
        """
        line_items = []
        
        # Pattern for line items: description, quantity, unit price, total
        # Example: "Product Name    5    $10.00    $50.00"
        pattern = r'([A-Za-z\s]+)\s+(\d+)\s+\$?([\d,]+\.?\d*)\s+\$?([\d,]+\.?\d*)'
        
        matches = re.finditer(pattern, text, re.MULTILINE)
        
        for match in matches:
            line_items.append({
                'description': match.group(1).strip(),
                'quantity': int(match.group(2)),
                'unit_price': float(match.group(3).replace(',', '')),
                'total': float(match.group(4).replace(',', ''))
            })
        
        return line_items
    
    def extract_fields(self, text: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract invoice fields from text.
        
        Args:
            text: Extracted text from OCR
            raw_data: Raw OCR data with bounding boxes
            
        Returns:
            Dictionary containing extracted fields
        """
        extracted = {
            'invoice_number': None,
            'invoice_date': None,
            'supplier': None,
            'total': None,
            'vat': None,
            'subtotal': None,
            'line_items': [],
            'confidence_scores': {}
        }
        
        try:
            # Extract each field
            for field, patterns in self.patterns.items():
                value = self._extract_with_pattern(text, patterns)
                if value:
                    extracted[field] = value
                    extracted['confidence_scores'][field] = DEFAULT_CONFIDENCE_SCORE
            
            # Extract line items
            extracted['line_items'] = self._extract_line_items(text)
            
            # Parse numeric values
            if extracted['total']:
                extracted['total'] = float(extracted['total'].replace(',', ''))
            if extracted['vat']:
                extracted['vat'] = float(extracted['vat'].replace(',', ''))
            if extracted['subtotal']:
                extracted['subtotal'] = float(extracted['subtotal'].replace(',', ''))
            
            return extracted
            
        except Exception as e:
            logger.error(f"Field extraction failed: {e}")
            return extracted


class SpacyNERExtractor(FieldExtractor):
    """Named Entity Recognition based field extraction using spaCy."""
    
    def __init__(self, model_name: str = "en_core_web_sm", confidence_threshold: float = 0.7):
        """
        Initialize spaCy NER extractor.
        
        Args:
            model_name: spaCy model to use
            confidence_threshold: Minimum confidence for field extraction
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        
        try:
            import spacy
            self.nlp = spacy.load(model_name)
        except Exception as e:
            logger.warning(f"Failed to load spaCy model: {e}. Falling back to pattern-based extraction.")
            self.nlp = None
    
    def extract_fields(self, text: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract invoice fields using NER.
        
        Args:
            text: Extracted text from OCR
            raw_data: Raw OCR data with bounding boxes
            
        Returns:
            Dictionary containing extracted fields
        """
        if not self.nlp:
            # Fallback to pattern-based extraction
            fallback = PatternBasedExtractor(self.confidence_threshold)
            return fallback.extract_fields(text, raw_data)
        
        try:
            doc = self.nlp(text)
            
            extracted = {
                'organizations': [],
                'dates': [],
                'money': [],
                'line_items': [],
                'confidence_scores': {}
            }
            
            # Extract named entities
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    extracted['organizations'].append(ent.text)
                elif ent.label_ == "DATE":
                    extracted['dates'].append(ent.text)
                elif ent.label_ == "MONEY":
                    extracted['money'].append(ent.text)
            
            # Use pattern-based extraction for specific fields
            pattern_extractor = PatternBasedExtractor(self.confidence_threshold)
            pattern_result = pattern_extractor.extract_fields(text, raw_data)
            
            # Merge results
            extracted.update(pattern_result)
            
            # Use NER results if pattern-based failed
            if not extracted['supplier'] and extracted['organizations']:
                extracted['supplier'] = extracted['organizations'][0]
            
            return extracted
            
        except Exception as e:
            logger.error(f"NER extraction failed: {e}")
            # Fallback to pattern-based extraction
            fallback = PatternBasedExtractor(self.confidence_threshold)
            return fallback.extract_fields(text, raw_data)


def create_field_extractor(extractor_type: str = "pattern_based", **kwargs) -> FieldExtractor:
    """
    Factory function to create field extractor.
    
    Args:
        extractor_type: Type of extractor (pattern_based, spacy_ner)
        **kwargs: Additional arguments for the extractor
        
    Returns:
        Field extractor instance
    """
    if extractor_type == "pattern_based":
        return PatternBasedExtractor(**kwargs)
    elif extractor_type == "spacy_ner":
        return SpacyNERExtractor(**kwargs)
    else:
        raise ValueError(f"Unknown extractor type: {extractor_type}")
