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

    # Augmentation
    num_augmentations: int = 2
    augmentation_semitone_range: int = 6

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
    max_checkpoints: int = 3
    seed: int = 42

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

    def validate(self):
        """Validate config values are in acceptable ranges."""
        errors = []

        if self.architecture not in ("lstm", "transformer"):
            errors.append(f"architecture must be 'lstm' or 'transformer', got '{self.architecture}'")
        if self.tokenizer not in ("legacy", "remi"):
            errors.append(f"tokenizer must be 'legacy' or 'remi', got '{self.tokenizer}'")
        if self.sequence_length <= 0:
            errors.append(f"sequence_length must be > 0, got {self.sequence_length}")
        if self.stride <= 0:
            errors.append(f"stride must be > 0, got {self.stride}")
        if not 0.0 < self.validation_split < 1.0:
            errors.append(f"validation_split must be in (0, 1), got {self.validation_split}")
        if self.batch_size <= 0:
            errors.append(f"batch_size must be > 0, got {self.batch_size}")
        if self.learning_rate <= 0:
            errors.append(f"learning_rate must be > 0, got {self.learning_rate}")
        if self.epochs <= 0:
            errors.append(f"epochs must be > 0, got {self.epochs}")
        if not 0.0 <= self.dropout < 1.0:
            errors.append(f"dropout must be in [0, 1), got {self.dropout}")
        if self.accumulation_steps < 1:
            errors.append(f"accumulation_steps must be >= 1, got {self.accumulation_steps}")
        if self.early_stopping_patience < 1:
            errors.append(f"early_stopping_patience must be >= 1, got {self.early_stopping_patience}")

        # Transformer-specific
        if self.architecture == "transformer":
            if self.sequence_length > self.max_seq_len:
                errors.append(
                    f"sequence_length ({self.sequence_length}) must be <= max_seq_len ({self.max_seq_len})"
                )
            if self.d_model % self.n_heads != 0:
                errors.append(
                    f"d_model ({self.d_model}) must be divisible by n_heads ({self.n_heads})"
                )

        if errors:
            raise ValueError("Config validation failed:\n  " + "\n  ".join(errors))


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
    parser.add_argument("--seed", type=int, help="Override random seed")
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
    if args.seed is not None:
        config.seed = args.seed

    # Environment variable overrides (logged when active)
    for env_var, attr in [("INPUT_DIR", "input_dir"), ("OUTPUT_DIR", "output_dir"), ("MAESTRO_DIR", "maestro_dir")]:
        env_val = os.environ.get(env_var)
        if env_val:
            print(f"ENV override: {env_var}={env_val}")
            setattr(config, attr, env_val)

    config.validate()
    return config
