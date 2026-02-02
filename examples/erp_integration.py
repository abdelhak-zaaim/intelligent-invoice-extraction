"""Example script for ERP integration."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from invoice_extraction import InvoiceExtractionPipeline
from invoice_extraction.config import Config
from invoice_extraction.integration import create_erp_adapter
from invoice_extraction.utils import setup_logging


def main():
    """Main function to demonstrate ERP integration."""
    # Setup logging
    setup_logging(level="INFO")
    
    # Create configuration
    config = Config.default()
    
    # Initialize pipeline
    pipeline = InvoiceExtractionPipeline(config)
    
    # Create ERP adapter (choose: generic, sap, oracle)
    erp_type = "generic"  # Change this to 'sap' or 'oracle' for specific adapters
    erp_adapter = create_erp_adapter(erp_type)
    
    # Connect to ERP system
    erp_config = {
        'url': 'https://erp.example.com/api',
        'api_key': 'your-api-key-here'
    }
    
    if not erp_adapter.connect(erp_config):
        print("Failed to connect to ERP system")
        return
    
    print(f"✓ Connected to {erp_type.upper()} ERP system\n")
    
    # Example invoice path
    invoice_path = "data/sample_invoice.pdf"
    
    if not Path(invoice_path).exists():
        print(f"Invoice file not found: {invoice_path}")
        return
    
    # Process invoice with ERP integration
    print(f"Processing invoice: {invoice_path}\n")
    result = pipeline.process_invoice(
        invoice_path=invoice_path,
        output_name="extracted_invoice",
        erp_adapter=erp_adapter
    )
    
    # Display results
    print("\n" + "="*60)
    print("ERP INTEGRATION RESULTS")
    print("="*60)
    
    if result['success']:
        print("✓ Invoice processing completed\n")
        
        if 'stages' in result and 'erp_integration' in result['stages']:
            erp_result = result['stages']['erp_integration']
            if erp_result['success']:
                print("✓ Invoice pushed to ERP system")
                print(f"  Invoice ID: {erp_result.get('invoice_id', 'N/A')}")
                print(f"  ERP Reference: {erp_result.get('erp_reference', 'N/A')}")
            else:
                print("✗ ERP integration failed")
                print(f"  Error: {erp_result.get('error', 'Unknown')}")
    else:
        print("✗ Invoice processing failed")
    
    print("="*60)


if __name__ == "__main__":
    main()
