FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY . .

# Copy and make the startup script executable
RUN chmod +x start.sh

# The application runs on 8080 by default in Cloud Run
EXPOSE 8080

# Use the startup script to run migrations and start the server
ENTRYPOINT ["./start.sh"]
