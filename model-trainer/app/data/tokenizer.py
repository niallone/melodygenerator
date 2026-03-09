"""Tokenizer creation, saving, and loading."""

import os


def create_remi_tokenizer():
    """Create a fresh MidiTok REMI tokenizer."""
    from miditok import REMI, TokenizerConfig

    config = TokenizerConfig(
        num_velocities=32,
        use_chords=True,
        use_rests=True,
        use_tempos=True,
    )
    return REMI(config)


def load_remi_tokenizer(path: str):
    """Load a saved REMI tokenizer from disk."""
    from miditok import REMI
    return REMI(params=path)


def save_tokenizer(tokenizer, path: str):
    """Save a tokenizer to disk."""
    os.makedirs(path, exist_ok=True)
    tokenizer.save(path)


def learn_bpe(tokenizer, midi_files: list[str], vocab_size: int):
    """Learn BPE compression on top of an existing tokenizer."""
    print(f"Learning BPE (vocab_size={vocab_size}) on {len(midi_files)} files...")
    tokenizer.learn_bpe(vocab_size=vocab_size, files_paths=midi_files)
    print(f"BPE learned. New vocab size: {len(tokenizer)}")
    return tokenizer
