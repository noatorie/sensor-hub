import logging
import yaml
import os
from importlib import import_module
from typing import Dict

from flask import request, abort, Flask, jsonify
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

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

# Enable CORS for your Next.js frontend
CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

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

load_sensors()
logger.info(f"Sensor Hub initialized with {len(sensors)} sensor(s)")


@app.route('/', methods=['GET'])
@app.route('/health', methods=['GET'])
def check_health():
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
    
    return jsonify({
        'status': overall_status,
        'sensors': sensor_status,
        'summary': {
            'total': len(sensors),
            'healthy': healthy_count,
            'unhealthy': unhealthy_count
        }
    }), 200 if overall_status == 'healthy' else 503


@app.route('/api/sensors', methods=['GET'])
def list_sensors():
    """List all available sensors"""
    api_key = request.headers.get('Authorization')
    if api_key != API_KEY:
        abort(401)
    
    sensor_list = []
    for sensor_id, sensor in sensors.items():
        sensor_list.append(sensor.get_info())
    
    return jsonify({
        'sensors': sensor_list,
        'count': len(sensor_list)
    })


@app.route('/api/sensors/<sensor_id>', methods=['GET'])
def get_sensor_data(sensor_id):
    """Get data from a specific sensor"""
    api_key = request.headers.get('Authorization')
    if api_key != API_KEY:
        abort(401)
    
    if sensor_id not in sensors:
        return jsonify({'error': f'Sensor {sensor_id} not found'}), 404
    
    sensor = sensors[sensor_id]
    result = sensor.read()
    
    if result['success']:
        return jsonify(result['data'])
    else:
        return jsonify({'error': result['error']}), 500


@app.route('/api/sensors/<sensor_id>/info', methods=['GET'])
def get_sensor_info(sensor_id):
    """Get information about a specific sensor"""
    api_key = request.headers.get('Authorization')
    if api_key != API_KEY:
        abort(401)
    
    if sensor_id not in sensors:
        return jsonify({'error': f'Sensor {sensor_id} not found'}), 404
    
    sensor = sensors[sensor_id]
    return jsonify(sensor.get_info())


# Legacy endpoint for backwards compatibility
@app.route('/api/temp-and-humid-sensor', methods=['GET'])
def get_sensor_data_legacy():
    """Legacy endpoint - redirects to DHT22 sensor"""
    api_key = request.headers.get('Authorization')
    if api_key != API_KEY:
        abort(401)

    
    # Try to find a DHT22 sensor for backwards compatibility
    dht22_sensor = None
    for sensor_id, sensor in sensors.items():
        if sensor.get_info()['type'] == 'DHT22':
            dht22_sensor = sensor
            break
    
    if dht22_sensor is None:
        return jsonify({'error': 'No DHT22 sensor configured'}), 404
    
    result = dht22_sensor.read()
    
    if result['success']:
        return jsonify(result['data'])
    else:
        return jsonify({'error': result['error']}), 500


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        # Cleanup sensors on shutdown
        for sensor in sensors.values():
            sensor.cleanup()
