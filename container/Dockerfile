# Dockerfile for NSZ - Nintendo Switch compression tool (optimized)
FROM python:3.11-alpine

# Container information labels
LABEL maintainer="NSZ Container"
LABEL description="NSZ Nintendo Switch compression tool in a container (optimized)"
LABEL version="2.0"

# Configure environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install minimal dependencies and NSZ in one layer
RUN apk add --no-cache \
    # Runtime dependencies for NSZ
    gcc \
    musl-dev \
    libffi-dev \
    && pip install --no-cache-dir nsz \
    # Clean up build dependencies
    && apk del gcc musl-dev libffi-dev

# Create directories for input/output files and keys
RUN mkdir -p /data /root/.switch \
    && echo "# Dummy keys file - replace with real prod.keys" > /root/.switch/prod.keys

# Set working directory
WORKDIR /data

# Configure working directory as volume
VOLUME ["/data"]

# Configure entry point to use nsz directly
ENTRYPOINT ["nsz"]

# Default command (show help if no arguments provided)
CMD ["--help"]