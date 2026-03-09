import asyncio
import base64
import json
import logging
import os
import tempfile
import uuid

import numpy as np
import torch
from midi2audio import FluidSynth
from music21 import chord, instrument, note, stream
from shared.models import MelodyLSTM

logger = logging.getLogger(__name__)


def _sample_with_top_k_top_p(logits, temperature=1.0, top_k=0, top_p=1.0):
    """
    Sample from logits with temperature, top-k, and top-p (nucleus) filtering.

    Args:
        logits: 1D tensor of raw logits.
        temperature: Temperature scaling factor.
        top_k: If > 0, keep only top-k logits.
        top_p: If < 1.0, keep smallest set of tokens with cumulative prob >= top_p.

    Returns:
        int: Sampled token index.
    """
    logits = logits / temperature

    # Top-k filtering
    if top_k > 0:
        top_k = min(top_k, logits.size(-1))
        values, _ = torch.topk(logits, top_k)
        min_val = values[-1]
        logits = torch.where(logits < min_val, torch.tensor(float("-inf")), logits)

    # Top-p (nucleus) filtering
    if top_p < 1.0:
        sorted_logits, sorted_indices = torch.sort(logits, descending=True)
        cumulative_probs = torch.cumsum(torch.softmax(sorted_logits, dim=-1), dim=-1)
        # Remove tokens with cumulative probability above the threshold
        sorted_indices_to_remove = cumulative_probs > top_p
        # Shift so that the first token above threshold is kept
        sorted_indices_to_remove[1:] = sorted_indices_to_remove[:-1].clone()
        sorted_indices_to_remove[0] = False
        indices_to_remove = sorted_indices[sorted_indices_to_remove]
        logits[indices_to_remove] = float("-inf")

    # Handle case where all logits are -inf after filtering
    if torch.all(logits == float("-inf")):
        # Fall back to uniform distribution over original top-k tokens
        if top_k > 0:
            k = min(top_k, logits.size(-1))
            uniform = torch.zeros_like(logits)
            uniform[:k] = 1.0 / k
            return int(np.random.choice(len(uniform.numpy()), p=uniform.numpy()))
        return int(np.random.randint(0, logits.size(-1)))

    probabilities = torch.softmax(logits, dim=-1).numpy()
    return int(np.random.choice(len(probabilities), p=probabilities))


def _load_pytorch_model(model_path, metadata_path, seeds_path):
    """
    Load a PyTorch model with its metadata and seeds.
    Supports v1 (legacy float), v2 (embedding), v3 (REMI), v4 (attention), v5 (transformer).

    Returns:
        tuple: (model, seeds, pitchnames, note_to_int, n_vocab, model_version, tokenizer)
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
            # Resolve relative to model directory
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

    return model, seeds, pitchnames, note_to_int, n_vocab, model_version, tokenizer


async def get_available_models(model_dir):
    """
    Load available models from the model directory.

    Supports two layouts:
    - Subdirectory: models/<name>/model.pt + metadata.json + seeds.json
    - Flat (legacy): models/<name>.pt + <name>_metadata.json + <name>_seeds.json

    Returns:
        dict: model_id -> (model, seeds, pitchnames, note_to_int, n_vocab, model_version, tokenizer)
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
                result = await loop.run_in_executor(None, _load_pytorch_model, model_path, metadata_path, seeds_path)
                models[model_id] = result
                model_version = result[5]
                architecture = "transformer" if hasattr(result[0], "d_model") else "lstm"
                logger.info(f"Loaded model: {model_id} (v{model_version}, {architecture})")
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
                result = await loop.run_in_executor(None, _load_pytorch_model, model_path, metadata_path, seeds_path)
                models[model_id] = result
                model_version = result[5]
                architecture = "transformer" if hasattr(result[0], "d_model") else "lstm"
                logger.info(f"Loaded model: {model_id} (v{model_version}, {architecture})")
            except Exception as e:
                logger.error(f"Error loading model {model_id}: {str(e)}")

    logger.debug(f"Returning models: {list(models.keys())}")
    return models


def _generate_notes_sync(
    model, seeds, pitchnames, n_vocab, num_notes=500, temperature=0.8, top_k=50, top_p=0.95, model_version=1
):
    """
    Generate notes using an LSTM model (any version).
    """
    int_to_note = dict((number, note_name) for number, note_name in enumerate(pitchnames))

    start = np.random.randint(0, len(seeds))
    pattern = np.array(seeds[start])

    prediction_output = []

    model.eval()
    with torch.no_grad():
        for _ in range(num_notes):
            if model_version >= 2:
                # Embedding-based: input is (1, seq_len) of int64
                if pattern.ndim == 2:
                    pattern_flat = pattern[:, 0].astype(np.int64)
                else:
                    pattern_flat = pattern.astype(np.int64)
                input_tensor = torch.LongTensor(pattern_flat).unsqueeze(0)
            else:
                # Legacy v1: input is (1, seq_len, 1) float / n_vocab
                prediction_input = np.reshape(pattern, (1, len(pattern), 1))
                prediction_input = prediction_input / float(n_vocab)
                input_tensor = torch.FloatTensor(prediction_input)

            logits = model(input_tensor)
            index = _sample_with_top_k_top_p(logits[0], temperature=temperature, top_k=top_k, top_p=top_p)

            result = int_to_note[index]
            prediction_output.append(result)

            if model_version >= 2:
                pattern = np.append(pattern, index)
                pattern = pattern[1:]
            else:
                pattern = np.append(pattern, [[index]], axis=0)
                pattern = pattern[1:]

    return prediction_output


def _generate_notes_remi_sync(
    model, seeds, tokenizer, n_vocab, num_notes=500, temperature=0.8, top_k=50, top_p=0.95, model_version=3
):
    """
    Generate token IDs using an LSTM/attention model with REMI tokenizer.
    Returns list of token IDs.
    """
    start = np.random.randint(0, len(seeds))
    pattern = np.array(seeds[start], dtype=np.int64)
    if pattern.ndim == 2:
        pattern = pattern[:, 0]

    generated_ids = []

    model.eval()
    with torch.no_grad():
        for _ in range(num_notes):
            input_tensor = torch.LongTensor(pattern).unsqueeze(0)
            logits = model(input_tensor)
            index = _sample_with_top_k_top_p(logits[0], temperature=temperature, top_k=top_k, top_p=top_p)
            generated_ids.append(index)
            pattern = np.append(pattern, index)
            pattern = pattern[1:]

    return generated_ids


def _generate_notes_transformer_sync(
    model, seeds, n_vocab, num_notes=500, temperature=0.8, top_k=50, top_p=0.95, max_seq_len=512
):
    """
    Autoregressive generation with a Transformer model.
    """
    start = np.random.randint(0, len(seeds))
    sequence = list(np.array(seeds[start], dtype=np.int64).flatten())

    model.eval()
    with torch.no_grad():
        for _ in range(num_notes):
            # Truncate to max_seq_len
            input_seq = sequence[-max_seq_len:]
            input_tensor = torch.LongTensor([input_seq])
            logits = model(input_tensor)
            # Take logits at the last position
            next_logits = logits[0, -1, :]
            index = _sample_with_top_k_top_p(next_logits, temperature=temperature, top_k=top_k, top_p=top_p)
            sequence.append(index)

    # Return only the generated portion
    return sequence[len(np.array(seeds[start]).flatten()) :]


def _create_midi_sync(prediction_output, filename, midi_program=0):
    """
    Create a MIDI file from generated notes (legacy pitch-string format).
    """
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


def _create_midi_from_tokens_sync(token_ids, tokenizer, filename, midi_program=0):
    """
    Create a MIDI file from REMI token IDs using MidiTok's decoder.
    """
    logger.info(f"Creating MIDI from REMI tokens with program={midi_program}: {filename}")

    # MidiTok 3.x expects 2D input: [[token_ids]]
    if isinstance(token_ids, list) and token_ids and not isinstance(token_ids[0], list):
        token_ids = [token_ids]
    midi = tokenizer.decode(token_ids)
    # Set instrument program on all tracks
    for track in midi.tracks:
        track.program = midi_program
    midi.dump_midi(filename)
    logger.info(f"REMI MIDI file written: {filename}")


def _convert_midi_to_wav_sync(midi_path, wav_path, soundfont_path):
    """Convert a MIDI file to WAV using FluidSynth."""
    logger.info(f"Converting MIDI to WAV: {midi_path} -> {wav_path}")
    fs = FluidSynth(soundfont_path, sample_rate=44100)
    fs.midi_to_audio(midi_path, wav_path)
    logger.info(f"WAV conversion complete: {wav_path}")


def _midi_to_seed_sequence(seed_midi_b64, tokenizer, seq_length):
    """
    Convert base64-encoded MIDI to a seed sequence for continuation.
    """
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


async def generate_melody(
    model_id,
    models,
    output_dir,
    soundfont_path=None,
    midi_program=0,
    num_notes=500,
    temperature=0.8,
    top_k=50,
    top_p=0.95,
    seed_midi=None,
    key_signature=None,
    tempo=None,
    style=None,
):
    """
    Generate a new melody using the specified model.

    Returns:
        tuple: (midi_path, wav_path) paths to the generated files.
    """
    logger.debug(f"Generating melody with model_id: {model_id}")

    if model_id not in models:
        logger.error(f"Invalid model ID: {model_id}")
        raise ValueError(f"Invalid model ID: {model_id}")

    model, seeds, pitchnames, note_to_int, n_vocab, model_version, tokenizer = models[model_id]

    if seeds is None:
        raise ValueError(f"No seed sequences available for model {model_id}")

    loop = asyncio.get_event_loop()
    architecture = "transformer" if hasattr(model, "d_model") else "lstm"
    generated_ids = None
    generated_notes = None

    if architecture == "transformer":
        max_seq_len = getattr(model, "max_seq_len", 512)

        # Handle seed MIDI for continuation
        effective_seeds = seeds
        if seed_midi and tokenizer:
            seq_length = len(seeds[0]) if seeds else max_seq_len
            seed_seq = await loop.run_in_executor(None, _midi_to_seed_sequence, seed_midi, tokenizer, seq_length)
            effective_seeds = [seed_seq.tolist()]

        generated_ids = await loop.run_in_executor(
            None,
            _generate_notes_transformer_sync,
            model,
            effective_seeds,
            n_vocab,
            num_notes,
            temperature,
            top_k,
            top_p,
            max_seq_len,
        )
    elif tokenizer is not None:
        # REMI model (v3+)
        effective_seeds = seeds
        if seed_midi:
            seq_length = len(seeds[0]) if seeds else 100
            seed_seq = await loop.run_in_executor(None, _midi_to_seed_sequence, seed_midi, tokenizer, seq_length)
            effective_seeds = [seed_seq.tolist()]

        generated_ids = await loop.run_in_executor(
            None,
            _generate_notes_remi_sync,
            model,
            effective_seeds,
            tokenizer,
            n_vocab,
            num_notes,
            temperature,
            top_k,
            top_p,
            model_version,
        )
    else:
        # Legacy pitch-string model (v1/v2)
        generated_notes = await loop.run_in_executor(
            None,
            _generate_notes_sync,
            model,
            seeds,
            pitchnames,
            n_vocab,
            num_notes,
            temperature,
            top_k,
            top_p,
            model_version,
        )

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    timestamp = uuid.uuid4().hex[:12]
    midi_file = os.path.join(output_dir, f"generated_melody_{timestamp}.mid")
    wav_file = os.path.join(output_dir, f"generated_melody_{timestamp}.wav")

    # Create MIDI file
    if tokenizer is not None:
        await loop.run_in_executor(
            None, _create_midi_from_tokens_sync, generated_ids, tokenizer, midi_file, midi_program
        )
    else:
        await loop.run_in_executor(None, _create_midi_sync, generated_notes, midi_file, midi_program)

    logger.debug(f"MIDI file saved: {midi_file}")

    # Convert MIDI to WAV
    if soundfont_path and os.path.exists(soundfont_path):
        await loop.run_in_executor(None, _convert_midi_to_wav_sync, midi_file, wav_file, soundfont_path)
        logger.debug(f"WAV file saved: {wav_file}")
    else:
        wav_file = None
        logger.warning("SoundFont not found, skipping WAV conversion")

    return midi_file, wav_file


def _build_condition_prefix(tokenizer, key_signature=None, tempo=None, style=None):
    """Build condition prefix token IDs for conditional generation."""
    # This is used by Phase 10 - returns None if no conditions specified
    if not key_signature and not tempo and not style:
        return None
    # Will be implemented in Phase 10
    return None


async def generate_melody_streaming(
    model_id,
    models,
    num_notes=500,
    temperature=0.8,
    top_k=50,
    top_p=0.95,
    midi_program=0,
    key_signature=None,
    tempo=None,
    style=None,
):
    """
    Async generator that yields note events for WebSocket streaming.
    """
    if model_id not in models:
        raise ValueError(f"Invalid model ID: {model_id}")

    model, seeds, pitchnames, note_to_int, n_vocab, model_version, tokenizer = models[model_id]

    if seeds is None:
        raise ValueError(f"No seed sequences available for model {model_id}")

    architecture = "transformer" if hasattr(model, "d_model") else "lstm"

    if architecture == "transformer":
        max_seq_len = getattr(model, "max_seq_len", 512)
        start = np.random.randint(0, len(seeds))
        sequence = list(np.array(seeds[start], dtype=np.int64).flatten())

        model.eval()
        offset = 0.0
        with torch.no_grad():
            for i in range(num_notes):
                input_seq = sequence[-max_seq_len:]
                input_tensor = torch.LongTensor([input_seq])
                logits = model(input_tensor)
                next_logits = logits[0, -1, :]
                index = _sample_with_top_k_top_p(next_logits, temperature=temperature, top_k=top_k, top_p=top_p)
                sequence.append(index)

                # Decode single token to note event
                note_event = _token_to_note_event(index, tokenizer, i, offset)
                if note_event:
                    offset = note_event.get("offset", offset) + note_event.get("duration", 0.5)
                    yield note_event

                # Yield control periodically
                if i % 10 == 0:
                    await asyncio.sleep(0)

        # Return full sequence for MIDI/WAV generation
        yield {"type": "sequence_complete", "token_ids": sequence[len(np.array(seeds[start]).flatten()) :]}

    elif tokenizer is not None:
        # REMI streaming
        start = np.random.randint(0, len(seeds))
        pattern = np.array(seeds[start], dtype=np.int64).flatten()
        generated_ids = []

        model.eval()
        offset = 0.0
        with torch.no_grad():
            for i in range(num_notes):
                input_tensor = torch.LongTensor(pattern).unsqueeze(0)
                logits = model(input_tensor)
                index = _sample_with_top_k_top_p(logits[0], temperature=temperature, top_k=top_k, top_p=top_p)
                generated_ids.append(index)
                pattern = np.append(pattern, index)[1:]

                note_event = _token_to_note_event(index, tokenizer, i, offset)
                if note_event:
                    offset = note_event.get("offset", offset) + note_event.get("duration", 0.5)
                    yield note_event

                if i % 10 == 0:
                    await asyncio.sleep(0)

        yield {"type": "sequence_complete", "token_ids": generated_ids}

    else:
        # Legacy pitch-string streaming
        int_to_note = dict((number, note_name) for number, note_name in enumerate(pitchnames))
        start = np.random.randint(0, len(seeds))
        pattern = np.array(seeds[start])

        model.eval()
        offset = 0.0
        with torch.no_grad():
            for i in range(num_notes):
                if model_version >= 2:
                    if pattern.ndim == 2:
                        pattern_flat = pattern[:, 0].astype(np.int64)
                    else:
                        pattern_flat = pattern.astype(np.int64)
                    input_tensor = torch.LongTensor(pattern_flat).unsqueeze(0)
                else:
                    prediction_input = np.reshape(pattern, (1, len(pattern), 1))
                    prediction_input = prediction_input / float(n_vocab)
                    input_tensor = torch.FloatTensor(prediction_input)

                logits = model(input_tensor)
                index = _sample_with_top_k_top_p(logits[0], temperature=temperature, top_k=top_k, top_p=top_p)

                result = int_to_note[index]
                # Parse note for streaming
                if ("." in result) or result.isdigit():
                    pitch = int(result.split(".")[0])
                else:
                    try:
                        from music21 import pitch as m21pitch

                        pitch = m21pitch.Pitch(result).midi
                    except Exception:
                        pitch = 60

                yield {
                    "type": "note",
                    "index": i,
                    "pitch": pitch,
                    "velocity": 80,
                    "duration": 0.5,
                    "offset": offset,
                }
                offset += 0.5

                if model_version >= 2:
                    pattern = np.append(pattern, index)
                    pattern = pattern[1:]
                else:
                    pattern = np.append(pattern, [[index]], axis=0)
                    pattern = pattern[1:]

                if i % 10 == 0:
                    await asyncio.sleep(0)

        yield {"type": "sequence_complete", "notes": [int_to_note[idx] for idx in range(len(pitchnames))]}


def _token_to_note_event(token_id, tokenizer, index, current_offset):
    """Convert a REMI token ID to a note event dict for streaming."""
    if tokenizer is None:
        return None
    try:
        # Get token string representation
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
