"""
train_v7.py — Non-interactive MusicTransformer training script for H100 server.

Usage:
    python train_v7.py [--input-dir /path/to/midi] [--output-dir /path/to/output]
                       [--maestro-dir /path/to/maestro] [--model-name melody_generator_transformer_v7]

All hyperparameters are set as constants below. No interactive prompts.
"""

import os
import sys
import json
import argparse
import asyncio
import numpy as np

# Ensure the model-trainer app package and shared/ are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from shared.models import MusicTransformer
from app.model_trainer import TransformerTrainer
from app.midi_processor import MIDIProcessor
from app.utils import setup_gpu

# ---------------------------------------------------------------------------
# Hyperparameters (tuned for H100 + REMI vocab)
# ---------------------------------------------------------------------------

# Model architecture
D_MODEL = 512
N_HEADS = 8
N_LAYERS = 8
D_FF = 2048
MAX_SEQ_LEN = 512
DROPOUT = 0.1

# Training
EPOCHS = 100
BATCH_SIZE = 64
LEARNING_RATE = 3e-4
WEIGHT_DECAY = 0.01
GRAD_CLIP_MAX_NORM = 1.0
WARMUP_STEPS = 2000
ACCUMULATION_STEPS = 2
VALIDATION_SPLIT = 0.1
EARLY_STOPPING_PATIENCE = 15

# Data
SEQUENCE_LENGTH = 256
STRIDE = 64
BPE_VOCAB_SIZE = 512

# Defaults
DEFAULT_INPUT_DIR = "/app/input"
DEFAULT_OUTPUT_DIR = "/app/model"
DEFAULT_MODEL_NAME = "melody_generator_transformer_v7"


def parse_args():
    parser = argparse.ArgumentParser(description="Train MusicTransformer v7")
    parser.add_argument("--input-dir", default=os.environ.get("INPUT_DIR", DEFAULT_INPUT_DIR),
                        help="Directory containing MIDI files for training")
    parser.add_argument("--output-dir", default=os.environ.get("OUTPUT_DIR", DEFAULT_OUTPUT_DIR),
                        help="Directory to save trained model artifacts")
    parser.add_argument("--maestro-dir", default=os.environ.get("MAESTRO_DIR"),
                        help="Optional MAESTRO dataset directory")
    parser.add_argument("--model-name", default=os.environ.get("MODEL_NAME", DEFAULT_MODEL_NAME),
                        help="Name for the saved model files")
    return parser.parse_args()


async def train():
    args = parse_args()
    device = setup_gpu()

    input_dir = args.input_dir
    output_dir = args.output_dir
    model_name = args.model_name
    model_path = os.path.join(output_dir, f"{model_name}.pt")
    os.makedirs(output_dir, exist_ok=True)

    print(f"Input directory:  {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Model name:       {model_name}")

    # -----------------------------------------------------------------------
    # 1. Create REMI tokenizer and process MIDI files
    # -----------------------------------------------------------------------
    midi_processor = MIDIProcessor(tokenizer_type="REMI")
    print("Creating REMI tokenizer...")
    midi_processor.create_tokenizer()

    extra_dirs = []
    if args.maestro_dir and os.path.isdir(args.maestro_dir):
        print(f"Including MAESTRO dataset from: {args.maestro_dir}")
        extra_dirs.append(args.maestro_dir)

    # Learn BPE on top of REMI before data preparation
    print(f"Learning BPE (vocab_size={BPE_VOCAB_SIZE})...")
    midi_files = MIDIProcessor._find_midi_files(input_dir)
    for extra_dir in extra_dirs:
        midi_files.extend(MIDIProcessor._find_midi_files(extra_dir))
    midi_processor.tokenizer.learn_bpe(vocab_size=BPE_VOCAB_SIZE, files_paths=midi_files)
    print(f"BPE learned. New vocab size: {len(midi_processor.tokenizer)}")

    print("Processing MIDI files...")
    train_data, val_data = midi_processor.prepare_data(
        input_dir, extra_dirs=extra_dirs or None
    )

    # -----------------------------------------------------------------------
    # 2. Prepare sequences
    # -----------------------------------------------------------------------
    print(f"Preparing sequences (length={SEQUENCE_LENGTH}, stride={STRIDE})...")
    network_input, network_output, n_vocab, _, _ = midi_processor.prepare_sequences(
        train_data, SEQUENCE_LENGTH, stride=STRIDE
    )
    print(f"Sequences: {network_input.shape[0]}, Vocab size: {n_vocab}")

    # -----------------------------------------------------------------------
    # 3. Build MusicTransformer
    # -----------------------------------------------------------------------
    print("Building MusicTransformer...")
    model = MusicTransformer(
        n_vocab=n_vocab,
        d_model=D_MODEL,
        n_heads=N_HEADS,
        n_layers=N_LAYERS,
        d_ff=D_FF,
        max_seq_len=MAX_SEQ_LEN,
        dropout=DROPOUT,
    )
    print(f"Model parameters: {model.count_parameters():,}")

    # -----------------------------------------------------------------------
    # 4. Train
    # -----------------------------------------------------------------------
    print("Starting training...")
    trainer = TransformerTrainer(model, device=device)
    await trainer.train(
        network_input, network_output, model_path,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        n_vocab=n_vocab,
        learning_rate=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
        grad_clip_max_norm=GRAD_CLIP_MAX_NORM,
        validation_split=VALIDATION_SPLIT,
        early_stopping_patience=EARLY_STOPPING_PATIENCE,
        warmup_steps=WARMUP_STEPS,
        accumulation_steps=ACCUMULATION_STEPS,
    )

    # -----------------------------------------------------------------------
    # 5. Save tokenizer alongside model
    # -----------------------------------------------------------------------
    tokenizer_dir = os.path.join(output_dir, f"{model_name}_tokenizer")
    midi_processor.save_tokenizer(tokenizer_dir)
    print(f"Tokenizer saved to {tokenizer_dir}")

    # Update metadata with tokenizer info
    metadata_path = os.path.splitext(model_path)[0] + "_metadata.json"
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        metadata["tokenizer_type"] = "REMI"
        metadata["tokenizer_path"] = f"{model_name}_tokenizer"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f)

    print("Training complete.")


if __name__ == "__main__":
    asyncio.run(train())
