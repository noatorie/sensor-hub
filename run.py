"""Uvicorn runner for Sensor Hub"""

from main import app
import uvicorn
import os

if __name__ == "__main__":
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    workers = int(os.getenv('WORKERS', 1))
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        workers=workers,
        log_level="info",
        access_log=True
    )
