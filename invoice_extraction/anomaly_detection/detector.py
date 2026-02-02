"""Anomaly detection module for invoice data."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)


class AnomalyDetector(ABC):
    """Abstract base class for anomaly detection."""
    
    @abstractmethod
    def detect_anomalies(self, data: Dict[str, Any], 
                        historical_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Detect anomalies in invoice data.
        
        Args:
            data: Current invoice data
            historical_data: Historical invoice data for comparison
            
        Returns:
            Anomaly detection results
        """
        pass


class StatisticalAnomalyDetector(AnomalyDetector):
    """Statistical anomaly detection using z-score and IQR methods."""
    
    def __init__(self, threshold: float = 0.8):
        """
        Initialize statistical anomaly detector.
        
        Args:
            threshold: Anomaly threshold (0-1, higher means stricter)
        """
        self.threshold = threshold
        self.z_score_threshold = 3.0  # Standard z-score threshold
    
    def _calculate_z_score(self, value: float, values: List[float]) -> float:
        """
        Calculate z-score for a value.
        
        Args:
            value: Value to check
            values: List of historical values
            
        Returns:
            Z-score
        """
        if len(values) < 2:
            return 0.0
        
        mean = np.mean(values)
        std = np.std(values)
        
        if std == 0:
            return 0.0
        
        return abs((value - mean) / std)
    
    def _detect_outliers_iqr(self, value: float, values: List[float]) -> bool:
        """
        Detect outliers using IQR method.
        
        Args:
            value: Value to check
            values: List of historical values
            
        Returns:
            True if value is an outlier
        """
        if len(values) < 4:
            return False
        
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        return value < lower_bound or value > upper_bound
    
    def detect_anomalies(self, data: Dict[str, Any], 
                        historical_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Detect anomalies using statistical methods.
        
        Args:
            data: Current invoice data
            historical_data: Historical invoice data for comparison
            
        Returns:
            Anomaly detection results
        """
        anomalies = []
        scores = {}
        
        try:
            # If no historical data, perform rule-based checks only
            if not historical_data or len(historical_data) < 2:
                return self._rule_based_detection(data)
            
            # Extract numeric values from historical data
            historical_totals = [h.get('total', 0) for h in historical_data if h.get('total')]
            historical_vats = [h.get('vat', 0) for h in historical_data if h.get('vat')]
            
            # Check total amount
            if 'total' in data and data['total']:
                total = float(data['total'])
                
                if historical_totals:
                    z_score = self._calculate_z_score(total, historical_totals)
                    is_outlier = self._detect_outliers_iqr(total, historical_totals)
                    
                    scores['total_z_score'] = z_score
                    
                    if z_score > self.z_score_threshold or is_outlier:
                        anomalies.append({
                            'field': 'total',
                            'type': 'statistical_outlier',
                            'value': total,
                            'message': f'Total amount is unusual (z-score: {z_score:.2f})',
                            'severity': 'high' if z_score > 4 else 'medium'
                        })
            
            # Check VAT amount
            if 'vat' in data and data['vat'] and historical_vats:
                vat = float(data['vat'])
                z_score = self._calculate_z_score(vat, historical_vats)
                
                scores['vat_z_score'] = z_score
                
                if z_score > self.z_score_threshold:
                    anomalies.append({
                        'field': 'vat',
                        'type': 'statistical_outlier',
                        'value': vat,
                        'message': f'VAT amount is unusual (z-score: {z_score:.2f})',
                        'severity': 'medium'
                    })
            
            # Add rule-based checks
            rule_based = self._rule_based_detection(data)
            anomalies.extend(rule_based['anomalies'])
            scores.update(rule_based.get('scores', {}))
            
            return {
                'has_anomalies': len(anomalies) > 0,
                'anomalies': anomalies,
                'scores': scores,
                'total_anomalies': len(anomalies)
            }
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return {
                'has_anomalies': False,
                'anomalies': [],
                'scores': {},
                'error': str(e)
            }
    
    def _rule_based_detection(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform rule-based anomaly detection.
        
        Args:
            data: Invoice data
            
        Returns:
            Anomaly detection results
        """
        anomalies = []
        
        # Check for suspiciously round numbers
        if 'total' in data and data['total']:
            total = float(data['total'])
            if total > 0 and total % 1000 == 0 and total > 1000:
                anomalies.append({
                    'field': 'total',
                    'type': 'suspicious_pattern',
                    'value': total,
                    'message': 'Total is a very round number',
                    'severity': 'low'
                })
        
        # Check for duplicate line items
        if 'line_items' in data and data['line_items']:
            descriptions = [item.get('description', '').lower() for item in data['line_items']]
            if len(descriptions) != len(set(descriptions)):
                anomalies.append({
                    'field': 'line_items',
                    'type': 'duplicate_items',
                    'message': 'Duplicate line items detected',
                    'severity': 'medium'
                })
        
        # Check for missing supplier
        if not data.get('supplier'):
            anomalies.append({
                'field': 'supplier',
                'type': 'missing_critical_field',
                'message': 'Supplier information is missing',
                'severity': 'high'
            })
        
        # Check for unusually high VAT percentage
        if 'vat' in data and 'subtotal' in data:
            try:
                vat = float(data['vat'])
                subtotal = float(data['subtotal'])
                if subtotal > 0:
                    vat_percentage = (vat / subtotal) * 100
                    if vat_percentage > 30:
                        anomalies.append({
                            'field': 'vat',
                            'type': 'unusual_rate',
                            'value': vat_percentage,
                            'message': f'VAT rate is unusually high: {vat_percentage:.2f}%',
                            'severity': 'high'
                        })
            except (ValueError, TypeError, ZeroDivisionError):
                pass
        
        return {
            'has_anomalies': len(anomalies) > 0,
            'anomalies': anomalies,
            'scores': {},
            'total_anomalies': len(anomalies)
        }


class RuleBasedAnomalyDetector(AnomalyDetector):
    """Rule-based anomaly detection."""
    
    def __init__(self, threshold: float = 0.8):
        """
        Initialize rule-based anomaly detector.
        
        Args:
            threshold: Anomaly threshold
        """
        self.threshold = threshold
    
    def detect_anomalies(self, data: Dict[str, Any], 
                        historical_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Detect anomalies using business rules.
        
        Args:
            data: Current invoice data
            historical_data: Historical invoice data (not used in rule-based)
            
        Returns:
            Anomaly detection results
        """
        detector = StatisticalAnomalyDetector(self.threshold)
        return detector._rule_based_detection(data)


def create_anomaly_detector(detector_type: str = "statistical", **kwargs) -> AnomalyDetector:
    """
    Factory function to create anomaly detector.
    
    Args:
        detector_type: Type of detector (statistical, rule_based)
        **kwargs: Additional arguments for the detector
        
    Returns:
        Anomaly detector instance
    """
    if detector_type == "statistical":
        return StatisticalAnomalyDetector(**kwargs)
    elif detector_type == "rule_based":
        return RuleBasedAnomalyDetector(**kwargs)
    else:
        raise ValueError(f"Unknown detector type: {detector_type}")
