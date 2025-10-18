FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PDF processing and OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pdf-processor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY pdf-processor/ .

# Copy the root fitrep_extractor.py (single source of truth) - MUST be after pdf-processor copy
COPY fitrep_extractor.py /app/app/services/fitrep_extractor.py

# Create uploads directory
RUN mkdir -p /app/uploads

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]