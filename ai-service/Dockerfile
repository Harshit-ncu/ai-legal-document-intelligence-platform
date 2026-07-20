FROM python:3.11-slim

WORKDIR /app

# Install system dependencies: Tesseract OCR and Poppler (for pdf2image)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port and run the FastAPI app
# Use the PORT environment variable provided by Railway, defaulting to 8000
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
