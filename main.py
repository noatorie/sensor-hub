"""Sensor Hub - FastAPI Application"""

import logging
import yaml
import os
from importlib import import_module
from typing import Dict, Optional

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sensor Hub API",
    description="Modular sensor management system for Raspberry Pi",
    version="1.0.0"
)

# Load configuration
CONFIG_FILE = os.getenv('CONFIG_FILE', 'config.yaml')
with open(CONFIG_FILE, 'r') as f:
    config = yaml.safe_load(f)

API_KEY = os.getenv('API_KEY', config.get('api_key', 'Bearer your_secret_api_key'))
allowed_origins = config.get('cors_origins', [
    "http://localhost:3000",
    "http://192.168.50.42:3000",
    "https://kurisu.noatorie.com"
])

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize sensors from config
sensors: Dict[str, object] = {}


def load_sensors():
    """Load and initialize all sensors from configuration"""
    for sensor_config in config.get('sensors', []):
        if not sensor_config.get('enabled', True):
            logger.info(f"Skipping disabled sensor: {sensor_config['id']}")
            continue
        
        try:
            sensor_type = sensor_config['type']
            sensor_id = sensor_config['id']
            
            # Dynamically import the sensor class
            module_name = f"sensors.{sensor_type.lower()}"
            class_name = f"{sensor_type}Sensor"
            
            module = import_module(module_name)
            sensor_class = getattr(module, class_name)
            
            # Instantiate the sensor
            sensor_instance = sensor_class(
                sensor_id=sensor_id,
                name=sensor_config.get('name', sensor_id),
                config=sensor_config
            )
            
            sensors[sensor_id] = sensor_instance
            logger.info(f"Loaded sensor: {sensor_id} ({sensor_type})")
            
        except Exception as e:
            logger.error(f"Failed to load sensor {sensor_config.get('id')}: {e}")


def verify_api_key(authorization: Optional[str] = Header(None)):
    """Verify API key from Authorization header"""
    if authorization != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )


@app.on_event("startup")
async def startup_event():
    """Initialize sensors on startup"""
    load_sensors()
    logger.info(f"Sensor Hub initialized with {len(sensors)} sensor(s)")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup sensors on shutdown"""
    for sensor in sensors.values():
        sensor.cleanup()
    logger.info("Sensor Hub shutdown complete")


@app.get("/", tags=["Health"])
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint - tests all sensors"""
    healthy_count = 0
    unhealthy_count = 0
    sensor_status = {}
    
    for sensor_id, sensor in sensors.items():
        try:
            result = sensor.read()
            if result['success']:
                healthy_count += 1
                sensor_status[sensor_id] = 'healthy'
            else:
                unhealthy_count += 1
                sensor_status[sensor_id] = 'unhealthy'
        except Exception as e:
            unhealthy_count += 1
            sensor_status[sensor_id] = f'error: {str(e)}'
    
    overall_status = 'healthy' if unhealthy_count == 0 else 'degraded' if healthy_count > 0 else 'unhealthy'
    status_code = status.HTTP_200_OK if overall_status == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        status_code=status_code,
        content={
            'status': overall_status,
            'sensors': sensor_status,
            'summary': {
                'total': len(sensors),
                'healthy': healthy_count,
                'unhealthy': unhealthy_count
            }
        }
    )


@app.get("/api/sensors", tags=["Sensors"])
async def list_sensors(authorization: Optional[str] = Header(None)):
    """List all available sensors"""
    verify_api_key(authorization)
    
    sensor_list = []
    for sensor_id, sensor in sensors.items():
        sensor_list.append(sensor.get_info())
    
    return {
        'sensors': sensor_list,
        'count': len(sensor_list)
    }


@app.get("/api/sensors/{sensor_id}", tags=["Sensors"])
async def get_sensor_data(sensor_id: str, authorization: Optional[str] = Header(None)):
    """Get data from a specific sensor"""
    verify_api_key(authorization)
    
    if sensor_id not in sensors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Sensor {sensor_id} not found'
        )
    
    sensor = sensors[sensor_id]
    result = sensor.read()
    
    if result['success']:
        return result['data']
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result['error']
        )


@app.get("/api/sensors/{sensor_id}/info", tags=["Sensors"])
async def get_sensor_info(sensor_id: str, authorization: Optional[str] = Header(None)):
    """Get information about a specific sensor"""
    verify_api_key(authorization)
    
    if sensor_id not in sensors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Sensor {sensor_id} not found'
        )
    
    sensor = sensors[sensor_id]
    return sensor.get_info()


# Legacy endpoint for backwards compatibility
@app.get("/api/temp-and-humid-sensor", tags=["Legacy"])
async def get_sensor_data_legacy(authorization: Optional[str] = Header(None)):
    """Legacy endpoint - redirects to DHT22 sensor"""
    verify_api_key(authorization)
    
    # Try to find a DHT22 sensor for backwards compatibility
    dht22_sensor = None
    for sensor_id, sensor in sensors.items():
        if sensor.get_info()['type'] == 'DHT22':
            dht22_sensor = sensor
            break
    
    if dht22_sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='No DHT22 sensor configured'
        )
    
    result = dht22_sensor.read()
    
    if result['success']:
        return result['data']
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result['error']
        )
