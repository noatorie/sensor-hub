"""Base sensor class - all sensors should inherit from this"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseSensor(ABC):
    """Abstract base class for all sensors"""
    
    def __init__(self, sensor_id: str, name: str, config: Dict[str, Any]):
        """
        Initialize the sensor
        
        Args:
            sensor_id: Unique identifier for this sensor
            name: Human-readable name
            config: Sensor-specific configuration
        """
        self.sensor_id = sensor_id
        self.name = name
        self.config = config
        self.enabled = config.get('enabled', True)
        logger.info(f"Initializing sensor: {name} ({sensor_id})")
    
    @abstractmethod
    def read(self) -> Dict[str, Any]:
        """
        Read data from the sensor
        
        Returns:
            Dictionary with sensor readings
        """
        pass
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """
        Get sensor information and metadata
        
        Returns:
            Dictionary with sensor info (type, units, etc.)
        """
        pass
    
    def cleanup(self):
        """Cleanup resources when sensor is no longer needed"""
        pass
