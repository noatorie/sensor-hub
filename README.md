# Sensor Hub API

A modular sensor management system for Raspberry Pi 5, designed to run as a Kubernetes-deployed API.

## Features

- 🔌 **Modular Architecture** - Easy to add new sensors
- 🚀 **FastAPI** - Modern, fast async API framework
- 🐳 **Docker Support** - Container-ready with binary builds
- ☸️ **Kubernetes Ready** - Deployment manifests included
- 🔐 **API Key Authentication** - Secure your endpoints
- 📊 **Health Checks** - Monitor sensor status
- 🌐 **CORS Enabled** - Frontend-friendly

## Project Structure

```
sensor-hub/
├── main.py              # FastAPI application
├── run.py               # Uvicorn runner
├── app.py               # Legacy Flask app (deprecated)
├── config.yaml          # Sensor configuration
├── sensors/
│   ├── __init__.py
│   ├── base.py         # Base sensor class
│   └── dht22.py        # DHT22 implementation
├── Dockerfile          # Binary build (PyInstaller)
├── Dockerfile.standard # Standard Python build (recommended)
├── k8s-deployment.yaml # Kubernetes manifests
└── requirements.txt
```

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run with Python
python run.py

# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

### Docker Build

**Standard Build (Recommended):**
```bash
docker build -f Dockerfile.standard -t sensor-hub:latest .
docker run --privileged -p 5000:5000 -v ./config.yaml:/app/config.yaml sensor-hub:latest
```

**Binary Build (Smaller Image):**
```bash
docker build -t sensor-hub:latest .
docker run --privileged -p 5000:5000 -v ./config.yaml:/app/config.yaml sensor-hub:latest
```

> ⚠️ **Note:** The binary build may have GPIO compatibility issues. Use `Dockerfile.standard` if you encounter problems.

### Kubernetes Deployment

```bash
# Edit k8s-deployment.yaml with your config
kubectl apply -f k8s-deployment.yaml

# Check status
kubectl get pods -l app=sensor-hub
kubectl logs -f deployment/sensor-hub
```

## API Endpoints

### Health Check
```bash
GET /health
# Returns overall sensor health status
```

### List Sensors
```bash
GET /api/sensors
Authorization: Bearer your_secret_api_key

# Returns all configured sensors
```

### Read Sensor Data
```bash
GET /api/sensors/{sensor_id}
Authorization: Bearer your_secret_api_key

# Example: GET /api/sensors/dht22-room
```

### Sensor Info
```bash
GET /api/sensors/{sensor_id}/info
Authorization: Bearer your_secret_api_key

# Returns sensor metadata and capabilities
```

### Legacy Endpoint
```bash
GET /api/temp-and-humid-sensor
Authorization: Bearer your_secret_api_key

# Backwards compatible with old DHT22 endpoint
```

## Configuration

Edit `config.yaml`:

```yaml
api_key: "Bearer your_secret_api_key"

cors_origins:
  - "http://localhost:3000"
  - "https://your-domain.com"

sensors:
  - id: "dht22-room"
    type: "DHT22"
    name: "Living Room Sensor"
    enabled: true
    pin: "D4"
```

## Adding New Sensors

1. Create a new sensor class in `sensors/` (e.g., `sensors/bme280.py`)
2. Inherit from `BaseSensor` and implement `read()` and `get_info()`
3. Add sensor configuration to `config.yaml`
4. Restart the application

Example:
```python
# sensors/bme280.py
from .base import BaseSensor

class BME280Sensor(BaseSensor):
    def read(self):
        # Your sensor reading logic
        return {'success': True, 'data': {...}}
    
    def get_info(self):
        return {'sensor_id': self.sensor_id, ...}
```

## Environment Variables

- `CONFIG_FILE` - Path to config file (default: `config.yaml`)
- `API_KEY` - Override API key from config
- `HOST` - Server host (default: `0.0.0.0`)
- `PORT` - Server port (default: `5000`)
- `WORKERS` - Number of workers (default: `1`)

## WSGI vs ASGI

**WSGI (Web Server Gateway Interface)** - Old Flask/Gunicorn standard, synchronous
**ASGI (Asynchronous Server Gateway Interface)** - Modern FastAPI/Uvicorn standard, supports async

This project uses **FastAPI + Uvicorn (ASGI)** for better async performance and modern features.

## Production Deployment

For production, use Uvicorn with proper workers:

```bash
uvicorn main:app --host 0.0.0.0 --port 5000 --workers 1
```

> ⚠️ **GPIO Warning:** Use `--workers 1` for hardware access. Multiple workers can cause GPIO conflicts.

## License

MIT
