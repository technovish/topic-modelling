# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TRANSFORMERS_CACHE=/app/.cache

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (curl for healthcheck/debugging)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install CPU version of PyTorch to reduce image size significantly
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy requirements.txt to container
COPY requirements.txt .

# Install remaining Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the Hugging Face transformer model to cache it in the image during build
RUN python -c "from transformers import pipeline; pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')"

# Copy the rest of the application code
COPY . .

# Ensure standard directories exist
RUN mkdir -p charts generated_files data

# Expose the Flask port
EXPOSE 5001

# Command to initialize the database and run the server using gunicorn
CMD ["sh", "-c", "python setup_db.py && gunicorn --workers=2 --timeout 300 --bind=0.0.0.0:${PORT:-5001} server:app"]
