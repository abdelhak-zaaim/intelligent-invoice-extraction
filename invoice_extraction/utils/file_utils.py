"""Utility functions for file operations."""

from pathlib import Path
from typing import List
import logging

logger = logging.getLogger(__name__)


def get_supported_extensions() -> List[str]:
    """
    Get list of supported file extensions.
    
    Returns:
        List of supported extensions
    """
    return ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp']


def is_supported_file(file_path: str) -> bool:
    """
    Check if file is a supported invoice format.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file is supported
    """
    path = Path(file_path)
    return path.suffix.lower() in get_supported_extensions()


def find_invoices(directory: str) -> List[str]:
    """
    Find all invoice files in a directory.
    
    Args:
        directory: Directory to search
        
    Returns:
        List of invoice file paths
    """
    invoice_files = []
    dir_path = Path(directory)
    
    if not dir_path.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return invoice_files
    
    for ext in get_supported_extensions():
        invoice_files.extend([str(f) for f in dir_path.glob(f"*{ext}")])
        invoice_files.extend([str(f) for f in dir_path.glob(f"*{ext.upper()}")])
    
    return sorted(invoice_files)
