import os
import json
import asyncio
from config import load_config
from midi_processor import MIDIProcessor
from model_builder import ModelBuilder
from model_trainer import ModelTrainer
from utils import setup_gpu, select_directory


async def main():
    """
    The main function that orchestrates the entire model training process.

    Supports two tokenization modes:
      - legacy: music21 pitch strings (default for backward compat)
      - remi: MidiTok REMI tokenization (for v3+ models)

    And two architectures:
      - lstm: LSTM with optional embedding and attention
      - transformer: Music Transformer with ALiBi
    """
    config = load_config()
    device = setup_gpu()

    input_dir = select_directory(config.INPUT_BASE, "Select the input directory containing MIDI files:")
    if not input_dir:
        print("No input directory selected. Exiting.")
        return

    # Ask for tokenizer type
    tokenizer_type = _ask_choice(
        "Select tokenizer type:",
        ["legacy (pitch strings)", "remi (MidiTok REMI)"],
    )
    use_remi = tokenizer_type == 1

    # Ask for architecture
    architecture = _ask_choice(
        "Select architecture:",
        ["lstm", "lstm + attention", "transformer"],
    )

    model_name = input("Enter model name (e.g., melody_generator_lstm_v6): ").strip()
    if not model_name:
        model_name = "trained_model"

    model_path = os.path.join(config.MODEL_BASE, f"{model_name}.pt")
    os.makedirs(config.MODEL_BASE, exist_ok=True)

    # Create processor
    midi_processor = MIDIProcessor(tokenizer_type='REMI' if use_remi else None)

    if use_remi:
        print("Creating REMI tokenizer...")
        midi_processor.create_tokenizer()

    # Process MIDI files (include MAESTRO if configured)
    extra_dirs = []
    if config.MAESTRO_DIR and os.path.isdir(config.MAESTRO_DIR):
        print(f"Including MAESTRO dataset from: {config.MAESTRO_DIR}")
        extra_dirs.append(config.MAESTRO_DIR)

    print("Processing MIDI files...")
    train_data, val_data = midi_processor.prepare_data(input_dir, extra_dirs=extra_dirs or None)

    # Prepare sequences (use stride from config if available)
    stride = config.STRIDE
    print("Preparing sequences...")
    network_input, network_output, n_vocab, pitchnames, note_to_int = midi_processor.prepare_sequences(
        train_data, config.SEQUENCE_LENGTH, stride=stride
    )

    # Build model
    print("Building the model...")
    use_attention = architecture == 1
    use_transformer = architecture == 2

    if use_transformer:
        from shared.models import MusicTransformer
        model = MusicTransformer(
            n_vocab=n_vocab,
            d_model=config.D_MODEL,
            n_heads=config.N_HEADS,
            n_layers=config.N_LAYERS,
            d_ff=config.D_FF,
            max_seq_len=config.MAX_SEQ_LEN,
        )
    else:
        model_builder = ModelBuilder()
        model = model_builder.create_model(
            network_input, n_vocab,
            embedding_dim=128 if (use_remi or use_attention) else 128,
            use_attention=use_attention,
        )

    # Train
    print("Training the model...")
    trainer = ModelTrainer(model, device=device)

    if use_transformer:
        from model_trainer import TransformerTrainer
        trainer = TransformerTrainer(model, device=device)
        await trainer.train(
            network_input, network_output, model_path,
            epochs=config.EPOCHS,
            batch_size=config.BATCH_SIZE,
            n_vocab=n_vocab,
            learning_rate=config.LEARNING_RATE,
            weight_decay=config.WEIGHT_DECAY,
            grad_clip_max_norm=config.GRAD_CLIP_MAX_NORM,
            validation_split=config.VALIDATION_SPLIT,
            early_stopping_patience=config.EARLY_STOPPING_PATIENCE,
            warmup_steps=config.WARMUP_STEPS,
        )
    else:
        await trainer.train(
            network_input, network_output, model_path,
            epochs=config.EPOCHS,
            batch_size=config.BATCH_SIZE,
            pitchnames=pitchnames,
            note_to_int=note_to_int,
            learning_rate=config.LEARNING_RATE,
            weight_decay=config.WEIGHT_DECAY,
            grad_clip_max_norm=config.GRAD_CLIP_MAX_NORM,
            validation_split=config.VALIDATION_SPLIT,
            early_stopping_patience=config.EARLY_STOPPING_PATIENCE,
        )

    # Save REMI tokenizer alongside model
    if use_remi:
        tokenizer_dir = os.path.join(config.MODEL_BASE, f"{model_name}_tokenizer")
        midi_processor.save_tokenizer(tokenizer_dir)
        print(f"Tokenizer saved to {tokenizer_dir}")

        # Update metadata with tokenizer info
        metadata_path = os.path.splitext(model_path)[0] + '_metadata.json'
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            metadata['tokenizer_type'] = 'REMI'
            metadata['tokenizer_path'] = f"{model_name}_tokenizer"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)

    print("Model training complete.")


def _ask_choice(prompt, options):
    """Simple CLI choice selector. Returns 0-indexed choice."""
    print(f"\n{prompt}")
    for i, opt in enumerate(options):
        print(f"  {i + 1}. {opt}")
    while True:
        try:
            choice = int(input("Enter your choice: ")) - 1
            if 0 <= choice < len(options):
                return choice
        except ValueError:
            pass
        print("Invalid choice. Try again.")


if __name__ == "__main__":
    asyncio.run(main())
