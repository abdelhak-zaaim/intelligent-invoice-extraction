# Intelligent Invoice Extraction

A Python-based intelligent document processing pipeline for invoices. This system uses OCR and machine learning to extract fields (supplier, VAT, total, line items), validate data, and detect anomalies. The design is modular, research-oriented, and ERP-agnostic for easy integration with various ERP systems.

## Features

- 🔍 **OCR Text Extraction**: Supports multiple image formats (PDF, PNG, JPG, TIFF) with Tesseract OCR
- 🤖 **ML-Based Field Extraction**: Pattern-based and spaCy NER approaches for extracting invoice fields
- ✅ **Data Validation**: Comprehensive validation of extracted data with configurable rules
- 🚨 **Anomaly Detection**: Statistical and rule-based anomaly detection for fraud prevention
- 💾 **Export Capabilities**: Export extracted data in JSON and CSV formats
- 🔌 **ERP Integration**: Modular, ERP-agnostic design with adapters for SAP, Oracle, and generic systems
- ⚙️ **Configurable**: YAML-based configuration for all components
- 📊 **Batch Processing**: Process multiple invoices efficiently

## Architecture

The system follows a modular pipeline architecture:

```
Invoice → OCR → Field Extraction → Validation → Anomaly Detection → Export → ERP Integration
```

### Key Components

1. **OCR Module** (`invoice_extraction/ocr/`):
   - Abstract `OCREngine` interface
   - `TesseractOCR` implementation
   - `PDFOCREngine` for PDF documents
   - Image preprocessing capabilities

2. **ML Module** (`invoice_extraction/ml/`):
   - Abstract `FieldExtractor` interface
   - `PatternBasedExtractor` using regex patterns
   - `SpacyNERExtractor` using Named Entity Recognition
   - Extracts: invoice number, date, supplier, total, VAT, subtotal, line items

3. **Validation Module** (`invoice_extraction/validation/`):
   - `InvoiceValidator` for comprehensive data validation
   - Validates required fields, numeric values, VAT rates, dates, and line items
   - Configurable strict/lenient modes

4. **Anomaly Detection Module** (`invoice_extraction/anomaly_detection/`):
   - `StatisticalAnomalyDetector` using z-scores and IQR
   - `RuleBasedAnomalyDetector` for business rule violations
   - Detects outliers, suspicious patterns, and unusual values

5. **Export Module** (`invoice_extraction/export/`):
   - `JSONExporter` for JSON output
   - `CSVExporter` for CSV output with separate line items file
   - `MultiFormatExporter` for multiple formats simultaneously

6. **Integration Module** (`invoice_extraction/integration/`):
   - Abstract `ERPAdapter` interface
   - `GenericERPAdapter` for REST API-based systems
   - `SAPAdapter` for SAP-specific integration
   - `OracleAdapter` for Oracle ERP integration
   - `ERPIntegrationManager` for managing multiple adapters

## Installation

### Prerequisites

- Python 3.8 or higher
- Tesseract OCR (system dependency)

### Install Tesseract OCR

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

### Install Python Package

```bash
# Clone the repository
git clone https://github.com/abdelhak-zaaim/intelligent-invoice-extraction.git
cd intelligent-invoice-extraction

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Optional: Install spaCy model (for NER-based extraction)

```bash
python -m spacy download en_core_web_sm
```

## Quick Start

### 1. Process a Single Invoice

```python
from invoice_extraction import InvoiceExtractionPipeline
from invoice_extraction.config import Config

# Initialize pipeline with default configuration
config = Config.default()
pipeline = InvoiceExtractionPipeline(config)

# Process invoice
result = pipeline.process_invoice(
    invoice_path="path/to/invoice.pdf",
    output_name="extracted_invoice"
)

# Check results
if result['success']:
    print("Invoice processed successfully!")
    print(f"Supplier: {result['extracted_data']['supplier']}")
    print(f"Total: {result['extracted_data']['total']}")
```

### 2. Batch Processing

```python
from invoice_extraction import InvoiceExtractionPipeline
from invoice_extraction.config import Config

# Initialize pipeline
pipeline = InvoiceExtractionPipeline(Config.default())

# Process multiple invoices
invoice_files = ["invoice1.pdf", "invoice2.pdf", "invoice3.pdf"]
batch_result = pipeline.process_batch(
    invoice_paths=invoice_files,
    output_dir="output"
)

print(f"Processed: {batch_result['successful']}/{batch_result['total']}")
```

### 3. Custom Configuration

```python
from invoice_extraction.config import Config

# Load from YAML
config = Config.from_yaml("config.yaml")

# Or create programmatically
config = Config()
config.ocr.language = "fra"  # French
config.validation.required_fields = ["supplier", "total", "invoice_number"]
config.anomaly_detection.enabled = True

pipeline = InvoiceExtractionPipeline(config)
```

### 4. ERP Integration

```python
from invoice_extraction import InvoiceExtractionPipeline
from invoice_extraction.integration import create_erp_adapter

# Create ERP adapter
erp_adapter = create_erp_adapter("sap")  # or "oracle", "generic"

# Connect to ERP
erp_adapter.connect({
    'url': 'https://erp.company.com/api',
    'api_key': 'your-api-key'
})

# Process with ERP integration
pipeline = InvoiceExtractionPipeline()
result = pipeline.process_invoice(
    invoice_path="invoice.pdf",
    erp_adapter=erp_adapter
)
```

## Configuration

The system can be configured via YAML files or programmatically. See `config.yaml` for a complete example.

### Configuration Options

- **OCR**: Engine type, language, DPI, preprocessing
- **ML**: Extractor type, confidence threshold, spaCy model
- **Validation**: Required fields, VAT rates, strict mode
- **Anomaly Detection**: Algorithms, threshold, enabled/disabled
- **Export**: Output formats, directory, JSON formatting

## Example Scripts

The `examples/` directory contains ready-to-use scripts:

- `process_single_invoice.py`: Process a single invoice
- `batch_processing.py`: Process multiple invoices
- `erp_integration.py`: Demonstrate ERP integration

Run examples:
```bash
cd examples
python process_single_invoice.py
```

## ERP Integration

The system is designed to be ERP-agnostic with a clear adapter pattern:

### Creating a Custom ERP Adapter

```python
from invoice_extraction.integration import ERPAdapter

class CustomERPAdapter(ERPAdapter):
    def connect(self, config):
        # Implement connection logic
        pass
    
    def push_invoice(self, invoice_data):
        # Implement push logic
        pass
    
    def validate_connection(self):
        # Implement validation
        pass
    
    def transform_data(self, invoice_data):
        # Transform to ERP format
        pass
```

### Supported ERP Systems

- **Generic**: REST API-based systems
- **SAP**: SAP-specific field mapping
- **Oracle**: Oracle ERP integration
- **Custom**: Easy to extend for other systems

## Extracted Fields

The system extracts the following fields from invoices:

- **Invoice Number**: Unique invoice identifier
- **Invoice Date**: Date of invoice
- **Supplier**: Vendor/supplier name
- **Subtotal**: Amount before tax
- **VAT/Tax**: Tax amount
- **Total**: Total amount due
- **Line Items**: Individual items with:
  - Description
  - Quantity
  - Unit Price
  - Total

## Data Validation

Automatic validation includes:

- ✅ Required field presence
- ✅ Numeric field validation
- ✅ VAT rate validation
- ✅ Date format and reasonableness
- ✅ Line item calculations
- ✅ Subtotal + VAT = Total consistency

## Anomaly Detection

The system detects various anomalies:

- 📊 Statistical outliers (z-score, IQR)
- 🔍 Suspicious patterns (round numbers)
- ⚠️ Unusual VAT rates
- 🔄 Duplicate line items
- ❌ Missing critical fields

## Export Formats

### JSON Export
```json
{
  "invoice_number": "INV-2024-001",
  "supplier": "ABC Corp",
  "total": 1250.50,
  "line_items": [...]
}
```

### CSV Export
- Main invoice data in one CSV file
- Line items in a separate CSV file

## Project Structure

```
intelligent-invoice-extraction/
├── invoice_extraction/          # Main package
│   ├── __init__.py
│   ├── pipeline.py             # Main pipeline
│   ├── config/                 # Configuration
│   ├── ocr/                    # OCR engines
│   ├── ml/                     # Field extraction
│   ├── validation/             # Data validation
│   ├── anomaly_detection/      # Anomaly detection
│   ├── export/                 # Export functionality
│   ├── integration/            # ERP adapters
│   └── utils/                  # Utilities
├── examples/                   # Example scripts
├── data/                       # Sample data (user-provided)
├── output/                     # Output directory
├── tests/                      # Unit tests
├── config.yaml                 # Sample configuration
├── requirements.txt            # Dependencies
├── setup.py                    # Package setup
└── README.md                   # This file
```

## Research and Development

This project is designed to be research-oriented with:

- **Modular Architecture**: Easy to swap components for research
- **Clear Interfaces**: Abstract base classes for all major components
- **Extensible Design**: Simple to add new extractors, validators, or detectors
- **Configuration-driven**: Test different approaches without code changes
- **Logging**: Comprehensive logging for analysis

## Contributing

Contributions are welcome! Areas for improvement:

- Additional OCR engines (EasyOCR, Google Vision API)
- Deep learning-based field extraction
- More sophisticated anomaly detection algorithms
- Additional ERP adapters
- Performance optimizations
- More comprehensive test suite

## License

MIT License - see LICENSE file for details

## Acknowledgments

Built with:
- Tesseract OCR
- scikit-learn
- spaCy
- Pillow
- OpenCV

## Support

For issues, questions, or contributions, please open an issue on GitHub.
