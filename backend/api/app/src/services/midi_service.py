"""MIDI file creation, audio conversion, and seed sequence handling."""

import base64
import logging
import os
import tempfile

import numpy as np
from midi2audio import FluidSynth
from music21 import chord, instrument, note, stream

logger = logging.getLogger(__name__)


def create_midi_from_notes(prediction_output, filename, midi_program=0):
    """Create a MIDI file from generated notes (legacy pitch-string format)."""
    logger.info(f"Creating MIDI file with program={midi_program}: {filename}")

    offset = 0
    output_notes = []

    for pattern in prediction_output:
        if ("." in pattern) or pattern.isdigit():
            notes_in_chord = pattern.split(".")
            notes = []
            for current_note in notes_in_chord:
                new_note = note.Note(int(current_note))
                notes.append(new_note)
            new_chord = chord.Chord(notes)
            new_chord.offset = offset
            output_notes.append(new_chord)
        else:
            new_note = note.Note(pattern)
            new_note.offset = offset
            output_notes.append(new_note)

        offset += 0.5

    inst = instrument.Instrument()
    inst.midiProgram = midi_program

    part = stream.Part()
    part.insert(0, inst)
    for n in output_notes:
        part.append(n)

    midi_stream = stream.Score()
    midi_stream.insert(0, part)
    midi_stream.write("midi", fp=filename)
    logger.info(f"MIDI file written with instrument program {midi_program}")


def create_midi_from_tokens(token_ids, tokenizer, filename, midi_program=0):
    """Create a MIDI file from REMI token IDs using MidiTok's decoder."""
    logger.info(f"Creating MIDI from REMI tokens with program={midi_program}: {filename}")

    # MidiTok 3.x expects 2D input: [[token_ids]]
    if isinstance(token_ids, list) and token_ids and not isinstance(token_ids[0], list):
        token_ids = [token_ids]
    midi = tokenizer.decode(token_ids)
    for track in midi.tracks:
        track.program = midi_program
    midi.dump_midi(filename)
    logger.info(f"REMI MIDI file written: {filename}")


def convert_midi_to_wav(midi_path, wav_path, soundfont_path):
    """Convert a MIDI file to WAV using FluidSynth."""
    logger.info(f"Converting MIDI to WAV: {midi_path} -> {wav_path}")
    fs = FluidSynth(soundfont_path, sample_rate=44100)
    fs.midi_to_audio(midi_path, wav_path)
    logger.info(f"WAV conversion complete: {wav_path}")


def midi_to_seed_sequence(seed_midi_b64, tokenizer, seq_length):
    """Convert base64-encoded MIDI to a seed sequence for continuation."""
    midi_bytes = base64.b64decode(seed_midi_b64)
    with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp:
        tmp.write(midi_bytes)
        tmp_path = tmp.name

    try:
        from symusic import Score as SymScore

        score = SymScore(tmp_path)
        tokens = tokenizer.encode(score)
        if hasattr(tokens, "ids"):
            token_ids = tokens.ids
        elif isinstance(tokens, list) and len(tokens) > 0:
            if hasattr(tokens[0], "ids"):
                token_ids = tokens[0].ids
            else:
                token_ids = tokens
        else:
            token_ids = list(tokens)

        # Truncate or pad to seq_length
        if len(token_ids) > seq_length:
            token_ids = token_ids[-seq_length:]
        elif len(token_ids) < seq_length:
            token_ids = [0] * (seq_length - len(token_ids)) + token_ids

        return np.array(token_ids, dtype=np.int64)
    finally:
        os.unlink(tmp_path)


def token_to_note_event(token_id, tokenizer, index, current_offset):
    """Convert a REMI token ID to a note event dict for streaming."""
    if tokenizer is None:
        return None
    try:
        token_str = tokenizer.vocab[token_id] if token_id < len(tokenizer.vocab) else None
        if token_str and token_str.startswith("Pitch_"):
            pitch = int(token_str.split("_")[1])
            return {
                "type": "note",
                "index": index,
                "pitch": pitch,
                "velocity": 80,
                "duration": 0.5,
                "offset": current_offset,
            }
    except Exception:
        pass
    return None
