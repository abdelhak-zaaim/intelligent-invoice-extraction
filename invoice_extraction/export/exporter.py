"""Export module for saving extracted invoice data."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import json
import csv
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class Exporter(ABC):
    """Abstract base class for data exporters."""
    
    @abstractmethod
    def export(self, data: Dict[str, Any], output_path: str) -> bool:
        """
        Export data to file.
        
        Args:
            data: Data to export
            output_path: Path to output file
            
        Returns:
            True if export successful
        """
        pass


class JSONExporter(Exporter):
    """Export data to JSON format."""
    
    def __init__(self, pretty: bool = True):
        """
        Initialize JSON exporter.
        
        Args:
            pretty: If True, format JSON with indentation
        """
        self.pretty = pretty
    
    def export(self, data: Dict[str, Any], output_path: str) -> bool:
        """
        Export data to JSON file.
        
        Args:
            data: Data to export
            output_path: Path to output file
            
        Returns:
            True if export successful
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                if self.pretty:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, f, ensure_ascii=False)
            
            logger.info(f"Data exported to JSON: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            return False


class CSVExporter(Exporter):
    """Export data to CSV format."""
    
    def __init__(self):
        """Initialize CSV exporter."""
        pass
    
    def _flatten_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten nested data structure for CSV export.
        
        Args:
            data: Data to flatten
            
        Returns:
            Flattened data
        """
        flattened = {}
        
        for key, value in data.items():
            if key == 'line_items':
                # Skip line items in main CSV, they'll be in a separate file
                flattened['line_items_count'] = len(value) if value else 0
            elif key == 'confidence_scores':
                # Flatten confidence scores
                for score_key, score_value in (value or {}).items():
                    flattened[f'confidence_{score_key}'] = score_value
            elif isinstance(value, (dict, list)):
                # Convert complex types to JSON string
                flattened[key] = json.dumps(value)
            else:
                flattened[key] = value
        
        return flattened
    
    def export(self, data: Dict[str, Any], output_path: str) -> bool:
        """
        Export data to CSV file.
        
        Args:
            data: Data to export
            output_path: Path to output file
            
        Returns:
            True if export successful
        """
        try:
            # Flatten the data
            flattened = self._flatten_data(data)
            
            # Write main invoice data
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=flattened.keys())
                writer.writeheader()
                writer.writerow(flattened)
            
            logger.info(f"Data exported to CSV: {output_path}")
            
            # Export line items to separate CSV if present
            if 'line_items' in data and data['line_items']:
                line_items_path = output_path.replace('.csv', '_line_items.csv')
                self._export_line_items(data['line_items'], line_items_path)
            
            return True
            
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            return False
    
    def _export_line_items(self, line_items: List[Dict[str, Any]], output_path: str) -> bool:
        """
        Export line items to separate CSV file.
        
        Args:
            line_items: List of line items
            output_path: Path to output file
            
        Returns:
            True if export successful
        """
        try:
            if not line_items:
                return True
            
            # Get all possible field names
            fieldnames = set()
            for item in line_items:
                fieldnames.update(item.keys())
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
                writer.writeheader()
                writer.writerows(line_items)
            
            logger.info(f"Line items exported to CSV: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Line items CSV export failed: {e}")
            return False


class MultiFormatExporter(Exporter):
    """Export data to multiple formats."""
    
    def __init__(self, formats: List[str], pretty_json: bool = True):
        """
        Initialize multi-format exporter.
        
        Args:
            formats: List of formats to export (json, csv)
            pretty_json: If True, format JSON with indentation
        """
        self.formats = formats
        self.exporters = {
            'json': JSONExporter(pretty=pretty_json),
            'csv': CSVExporter()
        }
    
    def export(self, data: Dict[str, Any], output_path: str) -> bool:
        """
        Export data to multiple formats.
        
        Args:
            data: Data to export
            output_path: Base path for output files (without extension)
            
        Returns:
            True if all exports successful
        """
        success = True
        
        for format_type in self.formats:
            if format_type not in self.exporters:
                logger.warning(f"Unknown export format: {format_type}")
                continue
            
            # Generate output path with appropriate extension
            format_path = f"{output_path}.{format_type}"
            
            # Export using appropriate exporter
            exporter = self.exporters[format_type]
            if not exporter.export(data, format_path):
                success = False
        
        return success


def create_exporter(formats: List[str], **kwargs) -> Exporter:
    """
    Factory function to create exporter.
    
    Args:
        formats: List of export formats
        **kwargs: Additional arguments for the exporter
        
    Returns:
        Exporter instance
    """
    if len(formats) == 1:
        format_type = formats[0]
        if format_type == 'json':
            return JSONExporter(**kwargs)
        elif format_type == 'csv':
            return CSVExporter()
        else:
            raise ValueError(f"Unknown format: {format_type}")
    else:
        return MultiFormatExporter(formats, **kwargs)
