"""Configuration module for invoice extraction system."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class OCRConfig:
    """OCR configuration."""
    engine: str = "tesseract"  # tesseract, easyocr, etc.
    language: str = "eng"
    dpi: int = 300
    preprocessing: bool = True


@dataclass
class MLConfig:
    """Machine Learning configuration."""
    model_type: str = "pattern_based"  # pattern_based, spacy_ner, custom
    confidence_threshold: float = 0.7
    spacy_model: str = "en_core_web_sm"


@dataclass
class ValidationConfig:
    """Data validation configuration."""
    strict_mode: bool = False
    required_fields: list = field(default_factory=lambda: ["supplier", "total", "invoice_date"])
    vat_rates: list = field(default_factory=lambda: [0.0, 5.0, 10.0, 20.0])


@dataclass
class AnomalyDetectionConfig:
    """Anomaly detection configuration."""
    enabled: bool = True
    algorithms: list = field(default_factory=lambda: ["statistical", "rule_based"])
    threshold: float = 0.8


@dataclass
class ExportConfig:
    """Export configuration."""
    formats: list = field(default_factory=lambda: ["json", "csv"])
    output_dir: str = "output"
    pretty_json: bool = True


@dataclass
class Config:
    """Main configuration class."""
    ocr: OCRConfig = field(default_factory=OCRConfig)
    ml: MLConfig = field(default_factory=MLConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    anomaly_detection: AnomalyDetectionConfig = field(default_factory=AnomalyDetectionConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    
    @classmethod
    def from_yaml(cls, config_path: str) -> "Config":
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        
        return cls(
            ocr=OCRConfig(**config_dict.get('ocr', {})),
            ml=MLConfig(**config_dict.get('ml', {})),
            validation=ValidationConfig(**config_dict.get('validation', {})),
            anomaly_detection=AnomalyDetectionConfig(**config_dict.get('anomaly_detection', {})),
            export=ExportConfig(**config_dict.get('export', {}))
        )
    
    @classmethod
    def default(cls) -> "Config":
        """Create default configuration."""
        return cls()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'ocr': self.ocr.__dict__,
            'ml': self.ml.__dict__,
            'validation': self.validation.__dict__,
            'anomaly_detection': self.anomaly_detection.__dict__,
            'export': self.export.__dict__
        }
