import os

class Config:
    """
    Configuration class for the model trainer.

    This class holds all the configuration parameters for the model training process.
    It uses class attributes for simplicity, but could be extended to load from
    environment variables or a configuration file if needed.
    """

    # Base directory for input MIDI files
    INPUT_BASE = "/app/input"

    # Base directory for saving trained models
    MODEL_BASE = "/app/model"

    # Number of training epochs
    EPOCHS = 50

    # Batch size for training
    BATCH_SIZE = 64

    # Length of input sequences
    SEQUENCE_LENGTH = 100

    # Stride between sequences (1 = full overlap, higher = less overlap)
    STRIDE = 1

    # Training hyperparameters
    LEARNING_RATE = 1e-3
    WEIGHT_DECAY = 0.01
    GRAD_CLIP_MAX_NORM = 1.0
    VALIDATION_SPLIT = 0.1
    EARLY_STOPPING_PATIENCE = 10

    # MAESTRO dataset directory (optional, set to None to skip)
    MAESTRO_DIR = None

    # Transformer architecture parameters
    ARCHITECTURE = "lstm"  # "lstm" or "transformer"
    D_MODEL = 512
    N_HEADS = 8
    N_LAYERS = 8
    D_FF = 2048
    MAX_SEQ_LEN = 512
    WARMUP_STEPS = 2000

def load_config():
    """
    Load and return the configuration.

    This function could be extended to load configuration from environment
    variables or a file. Currently, it simply returns an instance of the Config class.

    Returns:
        Config: An instance of the Config class.
    """
    return Config()