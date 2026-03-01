import os
import random
import json
import numpy as np
from music21 import converter, note, chord, interval, pitch


class MIDIProcessor:
    """
    A class for processing MIDI files and preparing data for the neural network.

    Supports two modes:
      - Legacy: music21-based pitch string extraction (for backward compat)
      - REMI: MidiTok REMI tokenization (for v3+ models)
    """

    def __init__(self, tokenizer_type=None):
        """
        Args:
            tokenizer_type: None for legacy, 'REMI' for MidiTok REMI.
        """
        self.tokenizer_type = tokenizer_type
        self.tokenizer = None

    def create_tokenizer(self, midi_files=None):
        """Create a MidiTok REMI tokenizer."""
        from miditok import REMI, TokenizerConfig

        config = TokenizerConfig(
            num_velocities=32,
            use_chords=True,
            use_rests=True,
            use_tempos=True,
        )
        self.tokenizer = REMI(config)
        self.tokenizer_type = 'REMI'
        return self.tokenizer

    def save_tokenizer(self, path):
        """Save tokenizer configuration to disk."""
        if self.tokenizer is not None:
            os.makedirs(path, exist_ok=True)
            self.tokenizer.save(path)

    def load_tokenizer(self, path):
        """Load tokenizer from disk."""
        from miditok import REMI
        self.tokenizer = REMI(params=path)
        self.tokenizer_type = 'REMI'

    def prepare_data(self, midi_directory, extra_dirs=None, validation_split=0.1):
        """
        Process MIDI files and extract notes/tokens.
        Splits files into train/val BEFORE augmentation to prevent data leakage.

        Args:
            midi_directory: Primary directory with MIDI files.
            extra_dirs: Optional list of additional directories (e.g., MAESTRO).
            validation_split: Fraction of files held out for validation (augmentation skipped).

        Returns:
            tuple: (train_data, val_data) or just data if validation_split is 0.
        """
        print(f"Preparing data from directory: {midi_directory}")
        midi_files = self._find_midi_files(midi_directory)

        if extra_dirs:
            for extra_dir in extra_dirs:
                if extra_dir and os.path.isdir(extra_dir):
                    extra_files = self._find_midi_files(extra_dir)
                    print(f"Found {len(extra_files)} additional MIDI files in {extra_dir}")
                    midi_files.extend(extra_files)

        print(f"Total MIDI files found: {len(midi_files)}")

        if not midi_files:
            raise ValueError("No MIDI files found.")

        # Split files into train/val BEFORE augmentation
        random.shuffle(midi_files)
        val_size = max(1, int(len(midi_files) * validation_split))
        val_files = midi_files[:val_size]
        train_files = midi_files[val_size:]
        print(f"Train files: {len(train_files)}, Val files: {len(val_files)}")

        if self.tokenizer_type == 'REMI':
            train_data = self._prepare_data_remi(train_files, augment=True)
            val_data = self._prepare_data_remi(val_files, augment=False)
        else:
            train_data = self._prepare_data_legacy(train_files, augment=True)
            val_data = self._prepare_data_legacy(val_files, augment=False)

        return train_data, val_data

    @staticmethod
    def _find_midi_files(directory):
        """Recursively find all .mid files in a directory."""
        midi_files = []
        for root, _, files in os.walk(directory):
            for f in files:
                if f.endswith('.mid') or f.endswith('.midi'):
                    midi_files.append(os.path.join(root, f))
        return midi_files

    def _prepare_data_remi(self, midi_files, augment=True):
        """Tokenize MIDI files with MidiTok REMI, with optional data augmentation via pitch shifting."""
        from symusic import Score as SymScore

        all_tokens = []
        for midi_path in midi_files:
            print(f"Processing (REMI): {midi_path}")
            try:
                score = SymScore(midi_path)
                tokens = self.tokenizer.encode(score)
                if hasattr(tokens, 'ids'):
                    all_tokens.extend(tokens.ids)
                elif isinstance(tokens, list) and len(tokens) > 0:
                    if hasattr(tokens[0], 'ids'):
                        for t in tokens:
                            all_tokens.extend(t.ids)
                    else:
                        all_tokens.extend(tokens)

                # Data augmentation: pitch shift (only for training data)
                if augment:
                    for _ in range(2):
                        semitones = random.randint(-6, 6)
                        if semitones == 0:
                            continue
                        shifted = score.shift_pitch(semitones)
                        tokens = self.tokenizer.encode(shifted)
                        if hasattr(tokens, 'ids'):
                            all_tokens.extend(tokens.ids)
                        elif isinstance(tokens, list) and len(tokens) > 0:
                            if hasattr(tokens[0], 'ids'):
                                for t in tokens:
                                    all_tokens.extend(t.ids)
                            else:
                                all_tokens.extend(tokens)
            except Exception as e:
                print(f"Error processing {midi_path}: {str(e)}")

        print(f"Total REMI tokens: {len(all_tokens)}")
        if not all_tokens:
            raise ValueError("No tokens were extracted from MIDI files.")
        return all_tokens

    def _prepare_data_legacy(self, midi_files, augment=True):
        """Extract pitch strings using music21 (original behavior)."""
        notes = []
        for midi_path in midi_files:
            print(f"Processing file: {midi_path}")
            try:
                midi = converter.parse(midi_path)
                notes_to_parse = midi.flat.notes
                for element in notes_to_parse:
                    if isinstance(element, note.Note):
                        notes.append(str(element.pitch))
                    elif isinstance(element, chord.Chord):
                        notes.append('.'.join(str(n) for n in element.normalOrder))
            except Exception as e:
                print(f"Error processing {midi_path}: {str(e)}")

        print(f"Total notes extracted: {len(notes)}")
        if not notes:
            raise ValueError("No notes were extracted.")

        if augment:
            augmented_notes = self.augment_data(notes)
            print(f"Total notes after augmentation: {len(augmented_notes)}")
            return augmented_notes
        return notes

    def augment_data(self, notes, num_augmentations=2):
        """Augment extracted notes by transposing (legacy mode)."""
        augmented_notes = [notes]
        for _ in range(num_augmentations):
            transposition = random.randint(-6, 6)
            transposed_notes = []
            for note_str in notes:
                if '.' in note_str:
                    chord_notes = note_str.split('.')
                    transposed_chord = []
                    for n in chord_notes:
                        if n.strip():
                            try:
                                transposed_note = str(interval.Interval(transposition).transposePitch(pitch.Pitch(n)))
                                transposed_chord.append(transposed_note)
                            except Exception as e:
                                print(f"Error transposing note {n}: {str(e)}")
                    if transposed_chord:
                        transposed_notes.append('.'.join(transposed_chord))
                else:
                    if note_str.strip():
                        try:
                            transposed_note = str(interval.Interval(transposition).transposePitch(pitch.Pitch(note_str)))
                            transposed_notes.append(transposed_note)
                        except Exception as e:
                            print(f"Error transposing note {note_str}: {str(e)}")
            augmented_notes.append(transposed_notes)
        return [n for sublist in augmented_notes for n in sublist]

    def prepare_sequences(self, data, sequence_length=100, stride=1):
        """
        Prepare input sequences for the neural network.

        For REMI mode: data is a flat list of token IDs.
        For legacy mode: data is a list of pitch strings.

        Args:
            data: Input data (token IDs or pitch strings).
            sequence_length: Length of input sequences.
            stride: Step size between sequences (default=1). Higher values reduce dataset size and overlap.

        Returns:
            tuple: (network_input, network_output, n_vocab, pitchnames, note_to_int)
                   pitchnames and note_to_int are None for REMI mode.
        """
        print(f"Preparing sequences from {len(data)} items (stride={stride})...")
        if not data:
            raise ValueError("Empty data.")

        if self.tokenizer_type == 'REMI':
            return self._prepare_sequences_remi(data, sequence_length, stride)
        else:
            return self._prepare_sequences_legacy(data, sequence_length, stride)

    def _prepare_sequences_remi(self, tokens, sequence_length, stride=1):
        """Create sliding-window sequences from REMI token IDs."""
        n_vocab = len(self.tokenizer)

        network_input = []
        network_output = []
        for i in range(0, len(tokens) - sequence_length, stride):
            seq_in = tokens[i:i + sequence_length]
            seq_out = tokens[i + sequence_length]
            network_input.append(seq_in)
            network_output.append(seq_out)

        if not network_input:
            raise ValueError("No sequences could be prepared.")

        network_input = np.array(network_input, dtype=np.int64)
        network_output = np.array(network_output, dtype=np.int64)

        print(f"REMI sequences prepared. Input shape: {network_input.shape}, n_vocab: {n_vocab}")
        return network_input, network_output, n_vocab, None, None

    def _prepare_sequences_legacy(self, notes, sequence_length, stride=1):
        """Create sliding-window sequences from pitch strings (original behavior)."""
        pitchnames = sorted(set(notes))
        note_to_int = dict((note_val, number) for number, note_val in enumerate(pitchnames))

        network_input = []
        network_output = []
        for i in range(0, len(notes) - sequence_length, stride):
            sequence_in = notes[i:i + sequence_length]
            sequence_out = notes[i + sequence_length]
            network_input.append([note_to_int[char] for char in sequence_in])
            network_output.append(note_to_int[sequence_out])

        if not network_input:
            raise ValueError("No sequences could be prepared.")

        network_input = np.array(network_input, dtype=np.int64)
        network_output = np.array(network_output, dtype=np.int64)
        n_vocab = len(pitchnames)

        print(f"Legacy sequences prepared. Input shape: {network_input.shape}, n_vocab: {n_vocab}")
        return network_input, network_output, n_vocab, pitchnames, note_to_int
