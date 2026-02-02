"""Main pipeline for invoice extraction."""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from .config import Config
from .ocr import create_ocr_engine
from .ml import create_field_extractor
from .validation import create_validator
from .anomaly_detection import create_anomaly_detector
from .export import create_exporter
from .integration import ERPAdapter

logger = logging.getLogger(__name__)


class InvoiceExtractionPipeline:
    """
    Main pipeline for intelligent invoice extraction.
    
    This pipeline orchestrates the entire invoice processing workflow:
    1. OCR text extraction
    2. ML-based field extraction
    3. Data validation
    4. Anomaly detection
    5. Data export
    6. Optional ERP integration
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the invoice extraction pipeline.
        
        Args:
            config: Configuration object. If None, uses default configuration.
        """
        self.config = config or Config.default()
        
        # Initialize components
        self._initialize_components()
        
        logger.info("Invoice extraction pipeline initialized")
    
    def _initialize_components(self):
        """Initialize all pipeline components based on configuration."""
        # OCR engine
        self.ocr_engine = create_ocr_engine(
            engine_type=self.config.ocr.engine,
            language=self.config.ocr.language,
            dpi=self.config.ocr.dpi,
            preprocessing=self.config.ocr.preprocessing
        )
        
        # Field extractor
        self.field_extractor = create_field_extractor(
            extractor_type=self.config.ml.model_type,
            confidence_threshold=self.config.ml.confidence_threshold
        )
        
        # Validator
        self.validator = create_validator(
            required_fields=self.config.validation.required_fields,
            vat_rates=self.config.validation.vat_rates,
            strict_mode=self.config.validation.strict_mode
        )
        
        # Anomaly detector
        if self.config.anomaly_detection.enabled:
            detector_type = self.config.anomaly_detection.algorithms[0] \
                if self.config.anomaly_detection.algorithms else "statistical"
            self.anomaly_detector = create_anomaly_detector(
                detector_type=detector_type,
                threshold=self.config.anomaly_detection.threshold
            )
        else:
            self.anomaly_detector = None
        
        # Exporter
        self.exporter = create_exporter(
            formats=self.config.export.formats,
            pretty_json=self.config.export.pretty_json
        )
    
    def process_invoice(self, 
                       invoice_path: str,
                       output_name: Optional[str] = None,
                       historical_data: Optional[List[Dict[str, Any]]] = None,
                       erp_adapter: Optional[ERPAdapter] = None) -> Dict[str, Any]:
        """
        Process a single invoice through the complete pipeline.
        
        Args:
            invoice_path: Path to the invoice file (image or PDF)
            output_name: Name for output files (without extension)
            historical_data: Historical invoice data for anomaly detection
            erp_adapter: Optional ERP adapter for integration
            
        Returns:
            Processing results including extracted data and status
        """
        logger.info(f"Processing invoice: {invoice_path}")
        
        result = {
            'success': False,
            'invoice_path': invoice_path,
            'stages': {}
        }
        
        try:
            # Stage 1: OCR text extraction
            logger.info("Stage 1: OCR text extraction")
            ocr_result = self.ocr_engine.extract_text(invoice_path)
            result['stages']['ocr'] = {
                'success': ocr_result['success'],
                'text_length': len(ocr_result['text'])
            }
            
            if not ocr_result['success']:
                result['error'] = 'OCR extraction failed'
                return result
            
            # Stage 2: Field extraction
            logger.info("Stage 2: Field extraction")
            extracted_fields = self.field_extractor.extract_fields(
                ocr_result['text'],
                ocr_result['raw_data']
            )
            result['stages']['extraction'] = {
                'success': True,
                'fields_extracted': list(extracted_fields.keys())
            }
            result['extracted_data'] = extracted_fields
            
            # Stage 3: Data validation
            logger.info("Stage 3: Data validation")
            validation_result = self.validator.validate(extracted_fields)
            result['stages']['validation'] = {
                'valid': validation_result['valid'],
                'errors': validation_result['errors'],
                'warnings': validation_result['warnings']
            }
            result['validation'] = validation_result
            
            # Stage 4: Anomaly detection
            if self.anomaly_detector:
                logger.info("Stage 4: Anomaly detection")
                anomaly_result = self.anomaly_detector.detect_anomalies(
                    extracted_fields,
                    historical_data
                )
                result['stages']['anomaly_detection'] = {
                    'has_anomalies': anomaly_result['has_anomalies'],
                    'total_anomalies': anomaly_result.get('total_anomalies', 0)
                }
                result['anomalies'] = anomaly_result
            
            # Stage 5: Export data
            if output_name:
                logger.info("Stage 5: Exporting data")
                output_dir = Path(self.config.export.output_dir)
                output_dir.mkdir(exist_ok=True)
                
                output_path = str(output_dir / output_name)
                export_success = self.exporter.export(extracted_fields, output_path)
                result['stages']['export'] = {
                    'success': export_success,
                    'output_path': output_path
                }
            
            # Stage 6: ERP integration (optional)
            if erp_adapter:
                logger.info("Stage 6: ERP integration")
                push_result = erp_adapter.push_invoice(extracted_fields)
                result['stages']['erp_integration'] = push_result
            
            result['success'] = True
            logger.info("Invoice processing completed successfully")
            
        except Exception as e:
            logger.error(f"Invoice processing failed: {e}")
            result['error'] = str(e)
        
        return result
    
    def process_batch(self,
                     invoice_paths: List[str],
                     output_dir: Optional[str] = None,
                     erp_adapter: Optional[ERPAdapter] = None) -> Dict[str, Any]:
        """
        Process multiple invoices in batch.
        
        Args:
            invoice_paths: List of paths to invoice files
            output_dir: Directory for output files
            erp_adapter: Optional ERP adapter for integration
            
        Returns:
            Batch processing results
        """
        logger.info(f"Processing batch of {len(invoice_paths)} invoices")
        
        if output_dir:
            self.config.export.output_dir = output_dir
        
        results = []
        successful = 0
        failed = 0
        
        for i, invoice_path in enumerate(invoice_paths):
            output_name = f"invoice_{i+1}" if output_dir else None
            
            result = self.process_invoice(
                invoice_path,
                output_name=output_name,
                erp_adapter=erp_adapter
            )
            
            if result['success']:
                successful += 1
            else:
                failed += 1
            
            results.append(result)
        
        logger.info(f"Batch processing completed: {successful} successful, {failed} failed")
        
        return {
            'total': len(invoice_paths),
            'successful': successful,
            'failed': failed,
            'results': results
        }
    
    def update_config(self, config: Config):
        """
        Update pipeline configuration and reinitialize components.
        
        Args:
            config: New configuration object
        """
        self.config = config
        self._initialize_components()
        logger.info("Pipeline configuration updated")
