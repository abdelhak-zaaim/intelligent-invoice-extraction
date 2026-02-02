"""ERP integration module for connecting with various ERP systems."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ERPAdapter(ABC):
    """Abstract base class for ERP adapters."""
    
    @abstractmethod
    def connect(self, config: Dict[str, Any]) -> bool:
        """
        Connect to ERP system.
        
        Args:
            config: Connection configuration
            
        Returns:
            True if connection successful
        """
        pass
    
    @abstractmethod
    def push_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Push invoice data to ERP system.
        
        Args:
            invoice_data: Extracted invoice data
            
        Returns:
            Result of the push operation
        """
        pass
    
    @abstractmethod
    def validate_connection(self) -> bool:
        """
        Validate connection to ERP system.
        
        Returns:
            True if connection is valid
        """
        pass
    
    @abstractmethod
    def transform_data(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform invoice data to ERP-specific format.
        
        Args:
            invoice_data: Extracted invoice data
            
        Returns:
            Transformed data in ERP format
        """
        pass


class GenericERPAdapter(ERPAdapter):
    """Generic ERP adapter for systems with REST APIs."""
    
    def __init__(self, erp_name: str = "Generic"):
        """
        Initialize generic ERP adapter.
        
        Args:
            erp_name: Name of the ERP system
        """
        self.erp_name = erp_name
        self.connected = False
        self.config = {}
    
    def connect(self, config: Dict[str, Any]) -> bool:
        """
        Connect to ERP system.
        
        Args:
            config: Connection configuration (url, api_key, etc.)
            
        Returns:
            True if connection successful
        """
        try:
            self.config = config
            
            # Validate required configuration
            required_fields = ['url', 'api_key']
            for field in required_fields:
                if field not in config:
                    logger.error(f"Missing required config field: {field}")
                    return False
            
            # In a real implementation, this would make an actual connection
            self.connected = True
            logger.info(f"Connected to {self.erp_name} ERP system")
            return True
            
        except Exception as e:
            logger.error(f"Connection to {self.erp_name} failed: {e}")
            return False
    
    def validate_connection(self) -> bool:
        """
        Validate connection to ERP system.
        
        Returns:
            True if connection is valid
        """
        return self.connected
    
    def transform_data(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform invoice data to generic ERP format.
        
        Args:
            invoice_data: Extracted invoice data
            
        Returns:
            Transformed data in ERP format
        """
        # Generic transformation - can be overridden by specific adapters
        return {
            'vendor': invoice_data.get('supplier', ''),
            'invoice_number': invoice_data.get('invoice_number', ''),
            'invoice_date': invoice_data.get('invoice_date', ''),
            'subtotal': invoice_data.get('subtotal', 0.0),
            'tax_amount': invoice_data.get('vat', 0.0),
            'total_amount': invoice_data.get('total', 0.0),
            'line_items': invoice_data.get('line_items', []),
            'metadata': {
                'extraction_confidence': invoice_data.get('confidence_scores', {}),
                'validation_status': invoice_data.get('validation_status', 'unknown'),
                'anomaly_flags': invoice_data.get('anomaly_flags', [])
            }
        }
    
    def push_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Push invoice data to ERP system.
        
        Args:
            invoice_data: Extracted invoice data
            
        Returns:
            Result of the push operation
        """
        if not self.connected:
            return {
                'success': False,
                'error': 'Not connected to ERP system'
            }
        
        try:
            # Transform data to ERP format
            transformed_data = self.transform_data(invoice_data)
            
            # In a real implementation, this would make an API call
            logger.info(f"Pushing invoice to {self.erp_name}: {transformed_data.get('invoice_number')}")
            
            return {
                'success': True,
                'message': f'Invoice pushed to {self.erp_name}',
                'invoice_id': transformed_data.get('invoice_number'),
                'erp_reference': f"ERP-{transformed_data.get('invoice_number')}"
            }
            
        except Exception as e:
            logger.error(f"Failed to push invoice to {self.erp_name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class SAPAdapter(GenericERPAdapter):
    """Adapter for SAP ERP systems."""
    
    def __init__(self):
        """Initialize SAP adapter."""
        super().__init__(erp_name="SAP")
    
    def transform_data(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform invoice data to SAP-specific format.
        
        Args:
            invoice_data: Extracted invoice data
            
        Returns:
            Transformed data in SAP format
        """
        # SAP-specific transformation
        base_data = super().transform_data(invoice_data)
        
        # Add SAP-specific fields
        sap_data = {
            'BUKRS': 'CompanyCode',  # Company code
            'LIFNR': base_data['vendor'],  # Vendor number
            'BLDAT': base_data['invoice_date'],  # Document date
            'WRBTR': base_data['total_amount'],  # Amount
            'WAERS': 'USD',  # Currency
            'XBLNR': base_data['invoice_number'],  # Reference
            'BSART': 'ZINV',  # Document type
            'ITEMS': base_data['line_items']
        }
        
        return sap_data


class OracleAdapter(GenericERPAdapter):
    """Adapter for Oracle ERP systems."""
    
    def __init__(self):
        """Initialize Oracle adapter."""
        super().__init__(erp_name="Oracle")
    
    def transform_data(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform invoice data to Oracle-specific format.
        
        Args:
            invoice_data: Extracted invoice data
            
        Returns:
            Transformed data in Oracle format
        """
        # Oracle-specific transformation
        base_data = super().transform_data(invoice_data)
        
        # Add Oracle-specific fields
        oracle_data = {
            'vendor_id': base_data['vendor'],
            'invoice_num': base_data['invoice_number'],
            'invoice_date': base_data['invoice_date'],
            'invoice_amount': base_data['total_amount'],
            'tax_amount': base_data['tax_amount'],
            'currency_code': 'USD',
            'invoice_type_lookup_code': 'STANDARD',
            'description': f"Invoice {base_data['invoice_number']}",
            'lines': base_data['line_items']
        }
        
        return oracle_data


class ERPIntegrationManager:
    """Manager class for handling multiple ERP integrations."""
    
    def __init__(self):
        """Initialize ERP integration manager."""
        self.adapters = {}
    
    def register_adapter(self, adapter_name: str, adapter: ERPAdapter) -> None:
        """
        Register an ERP adapter.
        
        Args:
            adapter_name: Name of the adapter
            adapter: ERP adapter instance
        """
        self.adapters[adapter_name] = adapter
        logger.info(f"Registered ERP adapter: {adapter_name}")
    
    def get_adapter(self, adapter_name: str) -> Optional[ERPAdapter]:
        """
        Get an ERP adapter by name.
        
        Args:
            adapter_name: Name of the adapter
            
        Returns:
            ERP adapter instance or None
        """
        return self.adapters.get(adapter_name)
    
    def list_adapters(self) -> list:
        """
        List all registered adapters.
        
        Returns:
            List of adapter names
        """
        return list(self.adapters.keys())


def create_erp_adapter(erp_type: str) -> ERPAdapter:
    """
    Factory function to create ERP adapter.
    
    Args:
        erp_type: Type of ERP system (generic, sap, oracle)
        
    Returns:
        ERP adapter instance
    """
    adapters = {
        'generic': GenericERPAdapter,
        'sap': SAPAdapter,
        'oracle': OracleAdapter
    }
    
    adapter_class = adapters.get(erp_type.lower())
    if not adapter_class:
        raise ValueError(f"Unknown ERP type: {erp_type}")
    
    return adapter_class()
