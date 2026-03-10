"""Data augmentation via pitch transposition."""

import random

from music21 import interval, pitch


def augment_remi(score, tokenizer, num_augmentations: int = 2, semitone_range: int = 6) -> list[int]:
    """Pitch-shift a symusic Score and return augmented REMI tokens."""
    tokens = []
    for _ in range(num_augmentations):
        semitones = random.randint(-semitone_range, semitone_range)
        if semitones == 0:
            continue
        shifted = score.shift_pitch(semitones)
        encoded = tokenizer.encode(shifted)
        tokens.extend(_extract_token_ids(encoded))
    return tokens


def augment_legacy(notes: list[str], num_augmentations: int = 2, semitone_range: int = 6) -> list[str]:
    """Transpose pitch strings by random intervals."""
    augmented = [notes]
    for _ in range(num_augmentations):
        transposition = random.randint(-semitone_range, semitone_range)
        transposed = []
        for note_str in notes:
            if "." in note_str:
                chord_notes = note_str.split(".")
                transposed_chord = []
                for n in chord_notes:
                    if n.strip():
                        try:
                            t = str(interval.Interval(transposition).transposePitch(pitch.Pitch(n)))
                            transposed_chord.append(t)
                        except Exception:
                            pass
                if transposed_chord:
                    transposed.append(".".join(transposed_chord))
            else:
                if note_str.strip():
                    try:
                        t = str(interval.Interval(transposition).transposePitch(pitch.Pitch(note_str)))
                        transposed.append(t)
                    except Exception:
                        pass
        augmented.append(transposed)
    return [n for sublist in augmented for n in sublist]


def _extract_token_ids(tokens) -> list[int]:
    """Extract flat list of token IDs from MidiTok encoding output."""
    if hasattr(tokens, "ids"):
        return list(tokens.ids)
    if isinstance(tokens, list) and len(tokens) > 0:
        if hasattr(tokens[0], "ids"):
            ids = []
            for t in tokens:
                ids.extend(t.ids)
            return ids
        return list(tokens)
    return []
