# Dockerfile
FROM python:3.10

# Install necessary packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && pip install --no-cache-dir ray[default]==2.31.0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /root

# Copy the entrypoint script
COPY entrypoint.sh /usr/local/bin/

# Make the entrypoint script executable
RUN chmod +x /usr/local/bin/entrypoint.sh

# Entrypoint script to start Ray
ENTRYPOINT ["entrypoint.sh"]
