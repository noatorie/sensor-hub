# ⚠️ WARNING: PyInstaller with GPIO libraries can be tricky!
# This builds a binary, but GPIO access may not work properly.
# If you encounter issues, use the standard Dockerfile.standard instead.

# Stage 1: Build binary using Python + PyInstaller
FROM python:3.11-slim AS builder
WORKDIR /app

# Install build dependencies for GPIO and PyInstaller
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    libgpiod2 \
    libgpiod-dev \
    binutils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY run.py .
COPY config.yaml .
COPY sensors/ sensors/

# Create a spec file for PyInstaller with hidden imports
RUN echo "# -*- mode: python ; coding: utf-8 -*-\n\
a = Analysis(\n\
    ['run.py'],\n\
    pathex=[],\n\
    binaries=[],\n\
    datas=[('config.yaml', '.'), ('sensors', 'sensors')],\n\
    hiddenimports=[\n\
        'uvicorn.logging',\n\
        'uvicorn.loops',\n\
        'uvicorn.loops.auto',\n\
        'uvicorn.protocols',\n\
        'uvicorn.protocols.http',\n\
        'uvicorn.protocols.http.auto',\n\
        'uvicorn.protocols.websockets',\n\
        'uvicorn.protocols.websockets.auto',\n\
        'uvicorn.lifespan',\n\
        'uvicorn.lifespan.on',\n\
        'board',\n\
        'adafruit_dht',\n\
        'sensors.dht22',\n\
        'sensors.base',\n\
    ],\n\
    hookspath=[],\n\
    hooksconfig={},\n\
    runtime_hooks=[],\n\
    excludes=[],\n\
    noarchive=False,\n\
)\n\
pyz = PYZ(a.pure)\n\
exe = EXE(\n\
    pyz,\n\
    a.scripts,\n\
    a.binaries,\n\
    a.datas,\n\
    [],\n\
    name='sensor-hub',\n\
    debug=False,\n\
    bootloader_ignore_signals=False,\n\
    strip=True,\n\
    upx=False,\n\
    upx_exclude=[],\n\
    runtime_tmpdir=None,\n\
    console=True,\n\
    disable_windowed_traceback=False,\n\
    argv_emulation=False,\n\
    target_arch=None,\n\
    codesign_identity=None,\n\
    entitlements_file=None,\n\
)" > sensor-hub.spec

# Build the binary
RUN pyinstaller sensor-hub.spec

# Stage 2: Minimal runtime image  
FROM debian:bookworm-slim
WORKDIR /app

# Install only runtime dependencies for GPIO
RUN apt-get update && apt-get install -y \
    libgpiod2 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy binary from builder
COPY --from=builder /app/dist/sensor-hub .

# Copy config (can be overridden by volume mount)
COPY config.yaml .

# Create non-root user
RUN useradd -m -u 1000 sensoruser && \
    chown -R sensoruser:sensoruser /app

# Expose port
EXPOSE 5000

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV CONFIG_FILE=/app/config.yaml

# Switch to non-root user (needs privileged mode for GPIO)
USER sensoruser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:5000/health || exit 1

# Run the binary
CMD ["./sensor-hub"]

