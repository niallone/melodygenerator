# Use the official PyTorch GPU image as the base image
FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime

# Set the working directory in the container
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app:/usr/src:$PYTHONPATH

# Install system dependencies
# libsndfile1 is required for audio file processing
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy shared models
COPY shared/ /usr/src/shared/

# Copy the project files into the container
COPY model-trainer/pyproject.toml .
COPY model-trainer/app/ app/

# Install Python dependencies
RUN pip install --no-cache-dir .

# Create non-root user
RUN useradd -m appuser
USER appuser

# Set the command to run the application
CMD ["python", "app/main.py"]
