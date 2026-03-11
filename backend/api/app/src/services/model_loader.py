"""Model discovery and loading from disk."""

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from typing import Any

import torch
from shared.models import MelodyLSTM

logger = logging.getLogger(__name__)


@dataclass
class ModelBundle:
    """All artefacts needed to run inference with a loaded model."""

    model: Any
    seeds: list | None
    pitchnames: list | None
    note_to_int: dict | None
    n_vocab: int
    model_version: int
    tokenizer: Any | None

    @property
    def architecture(self) -> str:
        return "transformer" if hasattr(self.model, "d_model") else "lstm"


def _load_pytorch_model(model_path, metadata_path, seeds_path):
    """Load a PyTorch model with its metadata and seeds.

    Supports LSTM (v1-v4) and Transformer architectures.

    Returns:
        ModelBundle with all artefacts needed for inference.
    """
    checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)
    n_vocab = checkpoint["n_vocab"]
    lstm_units = checkpoint.get("lstm_units", [512, 512, 512])
    dense_units = checkpoint.get("dense_units", 256)
    model_version = checkpoint.get("model_version", 1)
    embedding_dim = checkpoint.get("embedding_dim", 0)
    use_attention = checkpoint.get("use_attention", False)
    num_attention_heads = checkpoint.get("num_attention_heads", 4)
    architecture = checkpoint.get("architecture", "lstm")

    tokenizer = None

    if architecture == "transformer":
        from shared.models import MusicTransformer

        config = checkpoint.get("config", {})
        model = MusicTransformer(
            n_vocab=config.get("n_vocab", n_vocab),
            d_model=config.get("d_model", 256),
            n_heads=config.get("n_heads", 4),
            n_layers=config.get("n_layers", 4),
            d_ff=config.get("d_ff", 1024),
            max_seq_len=config.get("max_seq_len", 512),
            dropout=config.get("dropout", 0.1),
        )
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        model = MelodyLSTM(
            n_vocab,
            lstm_units=lstm_units,
            dense_units=dense_units,
            embedding_dim=embedding_dim,
            use_attention=use_attention,
            num_attention_heads=num_attention_heads,
        )
        model.load_state_dict(checkpoint["model_state_dict"])

    model.eval()

    # Load metadata
    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    pitchnames = metadata.get("pitchnames")
    note_to_int = metadata.get("note_to_int")
    tokenizer_type = metadata.get("tokenizer_type")

    # Load REMI tokenizer if applicable
    if tokenizer_type == "REMI":
        tokenizer_path = metadata.get("tokenizer_path")
        if tokenizer_path:
            model_dir = os.path.dirname(model_path)
            abs_tokenizer_path = os.path.join(model_dir, tokenizer_path)
            if os.path.isdir(abs_tokenizer_path):
                abs_tokenizer_path = os.path.join(abs_tokenizer_path, "tokenizer.json")
            if os.path.exists(abs_tokenizer_path):
                from miditok import REMI

                tokenizer = REMI(params=abs_tokenizer_path)

    # Load seeds
    seeds = None
    if os.path.exists(seeds_path):
        with open(seeds_path, "r") as f:
            seeds = json.load(f)

    return ModelBundle(
        model=model,
        seeds=seeds,
        pitchnames=pitchnames,
        note_to_int=note_to_int,
        n_vocab=n_vocab,
        model_version=model_version,
        tokenizer=tokenizer,
    )


async def get_available_models(model_dir):
    """Load available models from the model directory.

    Supports two layouts:
    - Subdirectory: models/<name>/model.pt + metadata.json + seeds.json
    - Flat (legacy): models/<name>.pt + <name>_metadata.json + <name>_seeds.json

    Returns:
        dict: model_id -> ModelBundle
    """
    logger.debug(f"Loading models from {model_dir}")

    if not os.path.exists(model_dir):
        logger.error(f"Model directory does not exist: {model_dir}")
        raise FileNotFoundError(f"Model directory not found: {model_dir}")

    models = {}
    loop = asyncio.get_event_loop()

    for entry in os.listdir(model_dir):
        entry_path = os.path.join(model_dir, entry)

        # Subdirectory layout: <model_dir>/<name>/model.pt
        if os.path.isdir(entry_path):
            model_path = os.path.join(entry_path, "model.pt")
            metadata_path = os.path.join(entry_path, "metadata.json")
            seeds_path = os.path.join(entry_path, "seeds.json")

            if not os.path.exists(model_path):
                continue

            model_id = entry

            if not os.path.exists(metadata_path):
                logger.warning(f"Skipping {model_id}: no metadata.json found")
                continue

            try:
                bundle = await loop.run_in_executor(None, _load_pytorch_model, model_path, metadata_path, seeds_path)
                models[model_id] = bundle
                logger.info(f"Loaded model: {model_id} (v{bundle.model_version}, {bundle.architecture})")
            except Exception as e:
                logger.error(f"Error loading model {model_id}: {str(e)}")

        # Flat layout (legacy): <model_dir>/<name>.pt
        elif entry.endswith(".pt"):
            model_id = os.path.splitext(entry)[0]
            model_path = entry_path
            metadata_path = os.path.join(model_dir, f"{model_id}_metadata.json")
            seeds_path = os.path.join(model_dir, f"{model_id}_seeds.json")

            if not os.path.exists(metadata_path):
                logger.warning(f"Skipping {model_id}: no metadata file found")
                continue

            try:
                bundle = await loop.run_in_executor(None, _load_pytorch_model, model_path, metadata_path, seeds_path)
                models[model_id] = bundle
                logger.info(f"Loaded model: {model_id} (v{bundle.model_version}, {bundle.architecture})")
            except Exception as e:
                logger.error(f"Error loading model {model_id}: {str(e)}")

    logger.debug(f"Returning models: {list(models.keys())}")
    return models
