"""Example script for processing a single invoice."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from invoice_extraction import InvoiceExtractionPipeline
from invoice_extraction.config import Config
from invoice_extraction.utils import setup_logging


def main():
    """Main function to process a single invoice."""
    # Setup logging
    setup_logging(level="INFO")
    
    # Create configuration
    config = Config.default()
    
    # Initialize pipeline
    pipeline = InvoiceExtractionPipeline(config)
    
    # Example invoice path (replace with your invoice)
    invoice_path = "data/sample_invoice.pdf"
    
    # Check if file exists
    if not Path(invoice_path).exists():
        print(f"Invoice file not found: {invoice_path}")
        print("Please place an invoice file in the data/ directory")
        return
    
    # Process invoice
    print(f"\nProcessing invoice: {invoice_path}\n")
    result = pipeline.process_invoice(
        invoice_path=invoice_path,
        output_name="extracted_invoice"
    )
    
    # Display results
    print("\n" + "="*60)
    print("PROCESSING RESULTS")
    print("="*60)
    
    if result['success']:
        print("✓ Processing completed successfully\n")
        
        # Show extracted data
        if 'extracted_data' in result:
            data = result['extracted_data']
            print("Extracted Fields:")
            print(f"  - Invoice Number: {data.get('invoice_number', 'N/A')}")
            print(f"  - Supplier: {data.get('supplier', 'N/A')}")
            print(f"  - Date: {data.get('invoice_date', 'N/A')}")
            print(f"  - Subtotal: {data.get('subtotal', 'N/A')}")
            print(f"  - VAT: {data.get('vat', 'N/A')}")
            print(f"  - Total: {data.get('total', 'N/A')}")
            print(f"  - Line Items: {len(data.get('line_items', []))}")
        
        # Show validation results
        if 'validation' in result:
            validation = result['validation']
            print(f"\nValidation: {'✓ PASSED' if validation['valid'] else '✗ FAILED'}")
            if validation['errors']:
                print("  Errors:")
                for error in validation['errors']:
                    print(f"    - {error}")
            if validation['warnings']:
                print("  Warnings:")
                for warning in validation['warnings']:
                    print(f"    - {warning}")
        
        # Show anomaly detection results
        if 'anomalies' in result:
            anomalies = result['anomalies']
            if anomalies['has_anomalies']:
                print(f"\n⚠ Anomalies Detected: {anomalies.get('total_anomalies', 0)}")
                for anomaly in anomalies.get('anomalies', []):
                    print(f"  - {anomaly.get('field', 'N/A')}: {anomaly.get('message', 'N/A')}")
            else:
                print("\n✓ No anomalies detected")
        
        # Show export information
        if 'stages' in result and 'export' in result['stages']:
            export_info = result['stages']['export']
            if export_info['success']:
                print(f"\n✓ Data exported to: {export_info['output_path']}")
    else:
        print("✗ Processing failed")
        if 'error' in result:
            print(f"  Error: {result['error']}")
    
    print("="*60)


if __name__ == "__main__":
    main()
