import os
import sys
import json
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'model-trainer', 'app'))

from midi_processor import MIDIProcessor
from model_builder import ModelBuilder
from model_trainer import ModelTrainer
from utils import setup_gpu

async def main():
    device = setup_gpu()

    input_dir = os.path.expanduser("~/midi-ai/models/training_data/v5_various")
    model_dir = os.path.expanduser("~/midi-ai/models")
    model_name = "melody_generator_lstm_v6"
    model_path = os.path.join(model_dir, f"{model_name}.pt")
    os.makedirs(model_dir, exist_ok=True)

    processor = MIDIProcessor(tokenizer_type='REMI')
    print("Creating REMI tokenizer...")
    processor.create_tokenizer()

    from symusic import Score as SymScore

    print("Processing MIDI files (no augmentation)...")
    midi_files = processor._find_midi_files(input_dir)
    print(f"Found {len(midi_files)} MIDI files")

    all_tokens = []
    for midi_path in midi_files:
        try:
            score = SymScore(midi_path)
            tokens = processor.tokenizer.encode(score)
            if hasattr(tokens, 'ids'):
                all_tokens.extend(tokens.ids)
            elif isinstance(tokens, list) and len(tokens) > 0:
                if hasattr(tokens[0], 'ids'):
                    for t in tokens:
                        all_tokens.extend(t.ids)
                else:
                    all_tokens.extend(tokens)
        except Exception as e:
            print(f"Error: {midi_path}: {e}")

    print(f"Total REMI tokens: {len(all_tokens)}")

    print("Preparing sequences...")
    network_input, network_output, n_vocab, _, _ = processor._prepare_sequences_remi(all_tokens, sequence_length=100)
    print(f"n_vocab: {n_vocab}, sequences: {len(network_input)}")

    model_builder = ModelBuilder()
    model = model_builder.create_model(network_input, n_vocab, embedding_dim=128, use_attention=False)

    trainer = ModelTrainer(model, device=device)
    await trainer.train(
        network_input, network_output, model_path,
        epochs=100,
        batch_size=256,
        pitchnames=None,
        note_to_int=None,
        learning_rate=4e-3,
        weight_decay=0.01,
        grad_clip_max_norm=1.0,
        validation_split=0.1,
        early_stopping_patience=10,
    )

    # Save tokenizer
    tokenizer_dir = os.path.join(model_dir, f"{model_name}_tokenizer")
    processor.save_tokenizer(tokenizer_dir)
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
        print("Metadata updated with tokenizer info")

    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
