"""Example script for batch processing multiple invoices."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from invoice_extraction import InvoiceExtractionPipeline
from invoice_extraction.config import Config
from invoice_extraction.utils import setup_logging, find_invoices


def main():
    """Main function to process multiple invoices in batch."""
    # Setup logging
    setup_logging(level="INFO")
    
    # Create configuration
    config = Config.default()
    
    # Initialize pipeline
    pipeline = InvoiceExtractionPipeline(config)
    
    # Find all invoices in data directory
    data_dir = "data"
    invoice_files = find_invoices(data_dir)
    
    if not invoice_files:
        print(f"No invoice files found in {data_dir}")
        print("Please place invoice files (PDF, PNG, JPG) in the data/ directory")
        return
    
    print(f"\nFound {len(invoice_files)} invoice(s) to process:")
    for i, invoice_path in enumerate(invoice_files, 1):
        print(f"  {i}. {Path(invoice_path).name}")
    
    # Process batch
    print(f"\nProcessing batch...\n")
    batch_result = pipeline.process_batch(
        invoice_paths=invoice_files,
        output_dir="output"
    )
    
    # Display results
    print("\n" + "="*60)
    print("BATCH PROCESSING RESULTS")
    print("="*60)
    print(f"Total invoices: {batch_result['total']}")
    print(f"Successful: {batch_result['successful']}")
    print(f"Failed: {batch_result['failed']}")
    print("="*60)
    
    # Display individual results
    for i, result in enumerate(batch_result['results'], 1):
        invoice_name = Path(result['invoice_path']).name
        status = "✓" if result['success'] else "✗"
        print(f"\n{i}. {invoice_name}: {status}")
        
        if result['success'] and 'extracted_data' in result:
            data = result['extracted_data']
            print(f"   Supplier: {data.get('supplier', 'N/A')}")
            print(f"   Total: {data.get('total', 'N/A')}")


if __name__ == "__main__":
    main()
