"""
Intelligent Invoice Extraction System

A modular, research-oriented, and ERP-agnostic invoice processing pipeline.
Supports OCR, ML-based field extraction, validation, and anomaly detection.
"""

__version__ = "0.1.0"

from .pipeline import InvoiceExtractionPipeline

__all__ = ["InvoiceExtractionPipeline"]
