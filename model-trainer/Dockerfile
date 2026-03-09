# Use the official PyTorch GPU image as the base image
FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime

# Set the working directory in the container
WORKDIR /usr/src

# Set environment variables
ENV PYTHONPATH=/usr/src:$PYTHONPATH

# Install system dependencies
# libsndfile1 is required for audio file processing
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy shared models
COPY shared/ /usr/src/shared/

# Copy the project files into the container
COPY model-trainer/pyproject.toml /usr/src/model-trainer/
COPY model-trainer/app/ /usr/src/model-trainer/app/
COPY model-trainer/configs/ /usr/src/model-trainer/configs/

# Install Python dependencies
WORKDIR /usr/src/model-trainer
RUN pip install --no-cache-dir .

# Create non-root user
RUN useradd -m appuser
USER appuser

# Default: train with a config file (override in docker-compose or CLI)
CMD ["python", "-m", "app.train", "--config", "configs/v8-transformer-bpe.yaml"]
