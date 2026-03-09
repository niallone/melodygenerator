"""MIDI data pipeline: file discovery, tokenization, augmentation, sequence preparation."""

import os
import random

import numpy as np
from music21 import converter, note, chord

from .augmentation import augment_remi, augment_legacy, _extract_token_ids
from .tokenizer import create_remi_tokenizer, learn_bpe, save_tokenizer


class MIDIDataPipeline:
    """End-to-end MIDI data pipeline for model training.

    Handles file discovery, tokenization (legacy or REMI with optional BPE),
    augmentation, train/val splitting, and sequence preparation.
    """

    def __init__(self, tokenizer_type: str = "remi"):
        self.tokenizer_type = tokenizer_type
        self.tokenizer = None

    def prepare(self, config) -> tuple:
        """Run the full data pipeline from config.

        Returns:
            (network_input, network_output, n_vocab) — numpy arrays ready for training.
        """
        # Discover MIDI files
        midi_files = find_midi_files(config.input_dir)
        if config.maestro_dir and os.path.isdir(config.maestro_dir):
            extra = find_midi_files(config.maestro_dir)
            print(f"Including {len(extra)} MAESTRO files from {config.maestro_dir}")
            midi_files.extend(extra)
        print(f"Total MIDI files: {len(midi_files)}")

        if not midi_files:
            raise ValueError("No MIDI files found.")

        # Create tokenizer
        if self.tokenizer_type == "remi":
            self.tokenizer = create_remi_tokenizer()
            if config.bpe_vocab_size:
                self.tokenizer = learn_bpe(self.tokenizer, midi_files, config.bpe_vocab_size)

        # Split files into train/val BEFORE augmentation
        random.shuffle(midi_files)
        val_size = max(1, int(len(midi_files) * config.validation_split))
        val_files = midi_files[:val_size]
        train_files = midi_files[val_size:]
        print(f"Train files: {len(train_files)}, Val files: {len(val_files)}")

        # Tokenize + augment
        if self.tokenizer_type == "remi":
            train_data = self._process_remi(train_files, augment=True)
            val_data = self._process_remi(val_files, augment=False)
        else:
            train_data = self._process_legacy(train_files, augment=True)
            val_data = self._process_legacy(val_files, augment=False)

        # Prepare sequences from training data
        network_input, network_output, n_vocab = self._prepare_sequences(
            train_data, config.sequence_length, config.stride
        )

        return network_input, network_output, n_vocab

    def save(self, path: str):
        """Save tokenizer to disk."""
        if self.tokenizer is not None:
            save_tokenizer(self.tokenizer, path)

    def _process_remi(self, midi_files: list[str], augment: bool = True) -> list[int]:
        """Tokenize MIDI files with REMI, with optional pitch-shift augmentation."""
        from symusic import Score as SymScore

        all_tokens = []
        for midi_path in midi_files:
            try:
                score = SymScore(midi_path)
                tokens = self.tokenizer.encode(score)
                all_tokens.extend(_extract_token_ids(tokens))

                if augment:
                    all_tokens.extend(augment_remi(score, self.tokenizer))
            except Exception as e:
                print(f"Error processing {midi_path}: {e}")

        print(f"Total REMI tokens: {len(all_tokens)}")
        if not all_tokens:
            raise ValueError("No tokens extracted from MIDI files.")
        return all_tokens

    def _process_legacy(self, midi_files: list[str], augment: bool = True) -> list[str]:
        """Extract pitch strings using music21."""
        notes = []
        for midi_path in midi_files:
            try:
                midi = converter.parse(midi_path)
                for element in midi.flat.notes:
                    if isinstance(element, note.Note):
                        notes.append(str(element.pitch))
                    elif isinstance(element, chord.Chord):
                        notes.append(".".join(str(n) for n in element.normalOrder))
            except Exception as e:
                print(f"Error processing {midi_path}: {e}")

        print(f"Total notes: {len(notes)}")
        if not notes:
            raise ValueError("No notes extracted.")

        if augment:
            notes = augment_legacy(notes)
            print(f"Total notes after augmentation: {len(notes)}")
        return notes

    def _prepare_sequences(self, data, sequence_length: int, stride: int) -> tuple:
        """Create sliding-window input/target pairs.

        Returns:
            (network_input, network_output, n_vocab)
        """
        print(f"Preparing sequences from {len(data)} items (length={sequence_length}, stride={stride})...")

        if self.tokenizer_type == "remi":
            return self._sequences_from_tokens(data, sequence_length, stride)
        else:
            return self._sequences_from_pitches(data, sequence_length, stride)

    def _sequences_from_tokens(self, tokens: list[int], seq_len: int, stride: int) -> tuple:
        """Sliding window over integer token IDs."""
        n_vocab = len(self.tokenizer)

        inputs, outputs = [], []
        for i in range(0, len(tokens) - seq_len, stride):
            inputs.append(tokens[i : i + seq_len])
            outputs.append(tokens[i + seq_len])

        if not inputs:
            raise ValueError("No sequences could be prepared.")

        network_input = np.array(inputs, dtype=np.int64)
        network_output = np.array(outputs, dtype=np.int64)
        print(f"Sequences: {network_input.shape[0]}, Vocab: {n_vocab}")
        return network_input, network_output, n_vocab

    def _sequences_from_pitches(self, notes: list[str], seq_len: int, stride: int) -> tuple:
        """Sliding window over pitch strings with integer encoding."""
        pitchnames = sorted(set(notes))
        note_to_int = {n: i for i, n in enumerate(pitchnames)}

        # Store for metadata saving
        self._pitchnames = pitchnames
        self._note_to_int = note_to_int

        inputs, outputs = [], []
        for i in range(0, len(notes) - seq_len, stride):
            inputs.append([note_to_int[n] for n in notes[i : i + seq_len]])
            outputs.append(note_to_int[notes[i + seq_len]])

        if not inputs:
            raise ValueError("No sequences could be prepared.")

        n_vocab = len(pitchnames)
        network_input = np.array(inputs, dtype=np.int64)
        network_output = np.array(outputs, dtype=np.int64)
        print(f"Sequences: {network_input.shape[0]}, Vocab: {n_vocab}")
        return network_input, network_output, n_vocab


def find_midi_files(directory: str) -> list[str]:
    """Recursively find all .mid/.midi files in a directory."""
    midi_files = []
    for root, _, files in os.walk(directory):
        for f in files:
            if f.endswith(".mid") or f.endswith(".midi"):
                midi_files.append(os.path.join(root, f))
    return midi_files
