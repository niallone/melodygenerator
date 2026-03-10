# Use Python 3.12 slim image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /usr/src/api

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/usr/src/api:/usr/src:$PYTHONPATH

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    fluidsynth \
    fluid-soundfont-gm \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared models
COPY shared/ /usr/src/shared/

# Copy project files
COPY backend/api/pyproject.toml .
COPY backend/api/app/ app/
COPY backend/api/wsgi.py .

# Install Python dependencies (use CPU-only PyTorch for smaller image)
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu .

# Create non-root user and output directory
RUN useradd -m appuser && \
    mkdir -p /usr/src/api/app/output && \
    chown appuser:appuser /usr/src/api/app/output
USER appuser

# Expose port
EXPOSE 4050

# Run the application using Uvicorn
CMD ["uvicorn", "wsgi:app", "--host", "0.0.0.0", "--port", "4050"]
