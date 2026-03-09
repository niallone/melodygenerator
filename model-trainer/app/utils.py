"""Utility functions for model training."""

import torch


def setup_gpu() -> torch.device:
    """Configure and return the best available PyTorch device."""
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print(f"GPU available: {torch.cuda.get_device_name(0)}")
        print(f"Number of GPUs: {torch.cuda.device_count()}")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = torch.device("mps")
        print("Apple Silicon MPS device available.")
    else:
        device = torch.device("cpu")
        print("No GPU/MPS found. Will use CPU.")
    return device
