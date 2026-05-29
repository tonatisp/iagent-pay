# Base Python Image
FROM python:3.11-slim

# Set Working Directory
WORKDIR /app

# Install System Dependencies (gcc and git are needed for compiling python dependencies)
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first for layer caching
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code into the container
COPY . /app/

# Install the local package
RUN pip install --no-cache-dir .

# Expose Nginx/Dashboard port
EXPOSE 8000

# Create a non-privileged user and group for security
RUN useradd -u 10001 -m appuser && \
    chown -R appuser:appuser /app

# Switch to non-privileged user
USER appuser

# Set entrypoint/CMD
CMD ["python", "serve_dashboard.py"]
