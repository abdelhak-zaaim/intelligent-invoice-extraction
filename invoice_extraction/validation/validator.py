"""Data validation module for invoice fields."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class Validator(ABC):
    """Abstract base class for validators."""
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate invoice data.
        
        Args:
            data: Invoice data to validate
            
        Returns:
            Validation result with errors and warnings
        """
        pass


class InvoiceValidator(Validator):
    """Validator for invoice data."""
    
    def __init__(self, required_fields: List[str], vat_rates: List[float], strict_mode: bool = False):
        """
        Initialize invoice validator.
        
        Args:
            required_fields: List of required field names
            vat_rates: List of valid VAT rates (percentages)
            strict_mode: If True, treat warnings as errors
        """
        self.required_fields = required_fields
        self.vat_rates = vat_rates
        self.strict_mode = strict_mode
    
    def _validate_required_fields(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate that all required fields are present.
        
        Args:
            data: Invoice data
            
        Returns:
            List of error messages
        """
        errors = []
        for field in self.required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Required field '{field}' is missing")
        return errors
    
    def _validate_numeric_fields(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate numeric fields (total, VAT, subtotal).
        
        Args:
            data: Invoice data
            
        Returns:
            List of error messages
        """
        errors = []
        
        # Check if numeric fields are valid
        for field in ['total', 'vat', 'subtotal']:
            if field in data and data[field] is not None:
                try:
                    value = float(data[field])
                    if value < 0:
                        errors.append(f"Field '{field}' cannot be negative")
                except (ValueError, TypeError):
                    errors.append(f"Field '{field}' must be a number")
        
        # Validate relationships between fields
        if 'subtotal' in data and 'vat' in data and 'total' in data:
            try:
                subtotal = float(data['subtotal'])
                vat = float(data['vat'])
                total = float(data['total'])
                
                expected_total = subtotal + vat
                if abs(expected_total - total) > 0.01:  # Allow small rounding errors
                    errors.append(
                        f"Total mismatch: subtotal ({subtotal}) + VAT ({vat}) = {expected_total}, "
                        f"but total is {total}"
                    )
            except (ValueError, TypeError):
                pass  # Already handled above
        
        return errors
    
    def _validate_vat_rate(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate VAT rate is within expected values.
        
        Args:
            data: Invoice data
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        if 'vat' in data and 'subtotal' in data:
            try:
                vat = float(data['vat'])
                subtotal = float(data['subtotal'])
                
                if subtotal > 0:
                    vat_rate = (vat / subtotal) * 100
                    
                    # Check if VAT rate is close to any expected rate
                    valid = False
                    for expected_rate in self.vat_rates:
                        if abs(vat_rate - expected_rate) < 0.5:  # Allow 0.5% tolerance
                            valid = True
                            break
                    
                    if not valid:
                        warnings.append(
                            f"Unusual VAT rate: {vat_rate:.2f}%. "
                            f"Expected rates: {', '.join(f'{r}%' for r in self.vat_rates)}"
                        )
            except (ValueError, TypeError, ZeroDivisionError):
                pass
        
        return warnings
    
    def _validate_date(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate invoice date.
        
        Args:
            data: Invoice data
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        if 'invoice_date' in data and data['invoice_date']:
            date_str = data['invoice_date']
            
            # Try to parse date
            date_formats = [
                '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d',
                '%d-%m-%Y', '%m-%d-%Y',
                '%d %b %Y', '%d %B %Y'
            ]
            
            parsed_date = None
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            
            if not parsed_date:
                warnings.append(f"Could not parse invoice date: {date_str}")
            else:
                # Check if date is in the future
                if parsed_date > datetime.now():
                    warnings.append(f"Invoice date is in the future: {date_str}")
                
                # Check if date is too old (more than 10 years)
                if (datetime.now() - parsed_date).days > 3650:
                    warnings.append(f"Invoice date is very old: {date_str}")
        
        return warnings
    
    def _validate_line_items(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate line items.
        
        Args:
            data: Invoice data
            
        Returns:
            List of error messages
        """
        errors = []
        
        if 'line_items' in data and data['line_items']:
            for i, item in enumerate(data['line_items']):
                # Check required fields
                if 'description' not in item:
                    errors.append(f"Line item {i+1}: missing description")
                if 'quantity' not in item:
                    errors.append(f"Line item {i+1}: missing quantity")
                if 'unit_price' not in item:
                    errors.append(f"Line item {i+1}: missing unit_price")
                if 'total' not in item:
                    errors.append(f"Line item {i+1}: missing total")
                
                # Validate calculations
                if all(k in item for k in ['quantity', 'unit_price', 'total']):
                    try:
                        expected = item['quantity'] * item['unit_price']
                        if abs(expected - item['total']) > 0.01:
                            errors.append(
                                f"Line item {i+1}: total mismatch "
                                f"({item['quantity']} × {item['unit_price']} = {expected}, "
                                f"but total is {item['total']})"
                            )
                    except (ValueError, TypeError):
                        pass
        
        return errors
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate invoice data.
        
        Args:
            data: Invoice data to validate
            
        Returns:
            Validation result with errors and warnings
        """
        errors = []
        warnings = []
        
        try:
            # Run all validations
            errors.extend(self._validate_required_fields(data))
            errors.extend(self._validate_numeric_fields(data))
            errors.extend(self._validate_line_items(data))
            
            warnings.extend(self._validate_vat_rate(data))
            warnings.extend(self._validate_date(data))
            
            # In strict mode, treat warnings as errors
            if self.strict_mode:
                errors.extend(warnings)
                warnings = []
            
            is_valid = len(errors) == 0
            
            return {
                'valid': is_valid,
                'errors': errors,
                'warnings': warnings,
                'data': data
            }
            
        except Exception as e:
            logger.error(f"Validation failed with exception: {e}")
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'data': data
            }


def create_validator(required_fields: List[str], vat_rates: List[float], 
                     strict_mode: bool = False) -> Validator:
    """
    Factory function to create validator.
    
    Args:
        required_fields: List of required field names
        vat_rates: List of valid VAT rates
        strict_mode: If True, treat warnings as errors
        
    Returns:
        Validator instance
    """
    return InvoiceValidator(required_fields, vat_rates, strict_mode)
