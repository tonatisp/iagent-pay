# Base Python Image
FROM python:3.11-slim

# Set Working Directory
WORKDIR /app

# Install System Dependencies (gcc needed for some crypto libs)
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install SDK
# In a real scenario, we'd install from PyPI. 
# Here we copy the local source code.
COPY . /app
RUN pip install --no-cache-dir .

# Default Command (Run the dashboard or a demo script)
# CMD ["python", "dashboard.py"]
# Or just keep container alive
CMD ["tail", "-f", "/dev/null"]
