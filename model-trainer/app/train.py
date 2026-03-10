"""Single entry point for model training.

Usage:
    python -m app.train --config configs/v8-transformer-bpe.yaml [--wandb]
    python -m app.train --config configs/v6-lstm-remi.yaml --input-dir /data/midi
"""

import asyncio
import os
import sys

# Ensure shared/ is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import load_config
from app.data import MIDIDataPipeline
from app.training import Trainer
from app.training.trainer import set_seed
from app.utils import setup_gpu


async def main():
    config = load_config()
    device = setup_gpu()

    print(f"Config: {config.name} ({config.architecture})")
    print(f"Input:  {config.input_dir}")
    print(f"Output: {config.output_dir}")
    if config.maestro_dir:
        print(f"MAESTRO: {config.maestro_dir}")

    # Seed before data pipeline for reproducible train/val splits
    set_seed(config.seed)

    # --- Data pipeline ---
    pipeline = MIDIDataPipeline(tokenizer_type=config.tokenizer)
    network_input, network_output, n_vocab = pipeline.prepare(config)

    # --- Build model ---
    if config.architecture == "transformer":
        from shared.models import MusicTransformer

        model = MusicTransformer(
            n_vocab=n_vocab,
            d_model=config.d_model,
            n_heads=config.n_heads,
            n_layers=config.n_layers,
            d_ff=config.d_ff,
            max_seq_len=config.max_seq_len,
            dropout=config.dropout,
        )
    else:
        from shared.models import MelodyLSTM

        model = MelodyLSTM(
            n_vocab,
            embedding_dim=config.embedding_dim,
            use_attention=config.use_attention,
            num_attention_heads=config.num_attention_heads,
        )

    # --- Experiment tracking ---
    tracker = None
    if config.wandb:
        from app.experiment_tracker import ExperimentTracker

        tracker = ExperimentTracker(
            project=config.wandb_project,
            run_name=config.name,
            config={
                "architecture": config.architecture,
                "tokenizer": config.tokenizer,
                "bpe_vocab_size": config.bpe_vocab_size,
                "epochs": config.epochs,
                "batch_size": config.batch_size,
                "learning_rate": config.learning_rate,
                "sequence_length": config.sequence_length,
                "seed": config.seed,
                "n_vocab": n_vocab,
            },
        )
        tracker.save_config_locally(config.output_dir)

    # --- Train ---
    trainer = Trainer(model, config, device=device)
    await trainer.train(network_input, network_output, experiment_tracker=tracker)

    # --- Save tokenizer ---
    if config.tokenizer == "remi":
        pipeline.save(config.tokenizer_dir)
        print(f"Tokenizer saved to {config.tokenizer_dir}")

    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
