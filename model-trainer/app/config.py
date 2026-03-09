"""Training configuration loaded from YAML files."""

import argparse
import os
from dataclasses import dataclass, field

import yaml


@dataclass
class TrainConfig:
    """All parameters for a training run."""

    # Identity
    name: str = "trained_model"
    architecture: str = "lstm"  # "lstm" or "transformer"

    # Tokenization
    tokenizer: str = "remi"  # "legacy" or "remi"
    bpe_vocab_size: int | None = None

    # Data
    input_dir: str = "/app/input"
    output_dir: str = "/app/model"
    maestro_dir: str | None = None
    sequence_length: int = 100
    stride: int = 1
    validation_split: float = 0.1

    # LSTM model
    embedding_dim: int = 128
    use_attention: bool = False
    num_attention_heads: int = 4

    # Transformer model
    d_model: int = 512
    n_heads: int = 8
    n_layers: int = 8
    d_ff: int = 2048
    max_seq_len: int = 512
    dropout: float = 0.1

    # Training
    epochs: int = 50
    batch_size: int = 64
    learning_rate: float = 1e-3
    weight_decay: float = 0.01
    grad_clip_max_norm: float = 1.0
    early_stopping_patience: int = 10
    warmup_steps: int = 0
    accumulation_steps: int = 1

    # Experiment tracking
    wandb: bool = False
    wandb_project: str = "melody-generator"

    @property
    def model_path(self) -> str:
        return os.path.join(self.output_dir, f"{self.name}.pt")

    @property
    def tokenizer_dir(self) -> str:
        return os.path.join(self.output_dir, f"{self.name}_tokenizer")

    @property
    def metadata_path(self) -> str:
        return os.path.splitext(self.model_path)[0] + "_metadata.json"

    @property
    def seeds_path(self) -> str:
        return os.path.splitext(self.model_path)[0] + "_seeds.json"


def load_config() -> TrainConfig:
    """Load config from YAML file with CLI overrides.

    Usage:
        python -m app.train --config configs/v8-transformer-bpe.yaml [--wandb] [--input-dir /path]
    """
    parser = argparse.ArgumentParser(description="Train a melody generation model")
    parser.add_argument("--config", required=True, help="Path to YAML config file")
    parser.add_argument("--input-dir", help="Override input directory")
    parser.add_argument("--output-dir", help="Override output directory")
    parser.add_argument("--maestro-dir", help="Override MAESTRO directory")
    parser.add_argument("--name", help="Override model name")
    parser.add_argument("--wandb", action="store_true", help="Enable W&B tracking")
    parser.add_argument("--epochs", type=int, help="Override number of epochs")
    args = parser.parse_args()

    # Load YAML
    with open(args.config) as f:
        raw = yaml.safe_load(f)

    config = TrainConfig(**{k: v for k, v in raw.items() if hasattr(TrainConfig, k)})

    # Apply CLI overrides
    if args.input_dir:
        config.input_dir = args.input_dir
    if args.output_dir:
        config.output_dir = args.output_dir
    if args.maestro_dir:
        config.maestro_dir = args.maestro_dir
    if args.name:
        config.name = args.name
    if args.wandb:
        config.wandb = True
    if args.epochs is not None:
        config.epochs = args.epochs

    # Also check environment variables as fallback
    config.input_dir = os.environ.get("INPUT_DIR", config.input_dir)
    config.output_dir = os.environ.get("OUTPUT_DIR", config.output_dir)
    if not config.maestro_dir:
        config.maestro_dir = os.environ.get("MAESTRO_DIR")

    return config
