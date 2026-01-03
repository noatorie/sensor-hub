"""DHT22 Temperature and Humidity Sensor"""

import board
import adafruit_dht
from typing import Dict, Any
import logging

from .base import BaseSensor

logger = logging.getLogger(__name__)


class DHT22Sensor(BaseSensor):
    """DHT22 temperature and humidity sensor"""
    
    def __init__(self, sensor_id: str, name: str, config: Dict[str, Any]):
        super().__init__(sensor_id, name, config)
        
        # Get GPIO pin from config (default to D4)
        pin_name = config.get('pin', 'D4')
        pin = getattr(board, pin_name)
        
        self.sensor = adafruit_dht.DHT22(pin)
        logger.info(f"DHT22 sensor initialized on pin {pin_name}")
    
    def read(self) -> Dict[str, Any]:
        """Read temperature and humidity from DHT22"""
        try:
            temperature_c = self.sensor.temperature
            humidity = self.sensor.humidity
            
            if humidity is not None and temperature_c is not None:
                temperature_f = temperature_c * (9 / 5) + 32
                return {
                    'success': True,
                    'data': {
                        'temperature_c': round(temperature_c, 1),
                        'temperature_f': round(temperature_f, 1),
                        'humidity': round(humidity, 1)
                    }
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to retrieve data from sensor'
                }
        
        except RuntimeError as error:
            # DHT sensors are finicky, runtime errors are common
            logger.warning(f"DHT22 read error: {error.args[0]}")
            return {
                'success': False,
                'error': f'RuntimeError: {error.args[0]}'
            }
        
        except Exception as error:
            logger.error(f"DHT22 unexpected error: {str(error)}")
            return {
                'success': False,
                'error': f'Exception: {str(error)}'
            }
    
    def get_info(self) -> Dict[str, Any]:
        """Get sensor information"""
        return {
            'sensor_id': self.sensor_id,
            'name': self.name,
            'type': 'DHT22',
            'description': 'Temperature and humidity sensor',
            'measurements': {
                'temperature_c': {
                    'unit': '°C',
                    'description': 'Temperature in Celsius'
                },
                'temperature_f': {
                    'unit': '°F',
                    'description': 'Temperature in Fahrenheit'
                },
                'humidity': {
                    'unit': '%',
                    'description': 'Relative humidity'
                }
            },
            'pin': self.config.get('pin', 'D4'),
            'enabled': self.enabled
        }
    
    def cleanup(self):
        """Clean up sensor resources"""
        try:
            self.sensor.exit()
            logger.info(f"DHT22 sensor {self.sensor_id} cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up DHT22 sensor: {e}")
