"""Melody generation orchestration: ties together model inference, sampling, and MIDI output."""

import asyncio
import logging
import os
import time
import uuid

import numpy as np
import torch

from .midi_service import (
    convert_midi_to_wav,
    create_midi_from_notes,
    create_midi_from_tokens,
    midi_to_seed_sequence,
    token_to_note_event,
)
from .model_loader import ModelBundle, get_available_models
from .sampling import sample_with_top_k_top_p

logger = logging.getLogger(__name__)

# Re-export for backward compatibility with api.py import
__all__ = ["ModelBundle", "get_available_models", "generate_melody", "generate_melody_streaming"]


def _generate_notes_sync(
    model, seeds, pitchnames, n_vocab, num_notes=500, temperature=0.8, top_k=50, top_p=0.95, model_version=1
):
    """Generate notes using an LSTM model (any version)."""
    int_to_note = dict((number, note_name) for number, note_name in enumerate(pitchnames))

    start = np.random.randint(0, len(seeds))
    pattern = np.array(seeds[start])

    prediction_output = []

    model.eval()
    with torch.no_grad():
        for _ in range(num_notes):
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
            index = sample_with_top_k_top_p(logits[0], temperature=temperature, top_k=top_k, top_p=top_p)

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
    """Generate token IDs using an LSTM/attention model with REMI tokenizer."""
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
            index = sample_with_top_k_top_p(logits[0], temperature=temperature, top_k=top_k, top_p=top_p)
            generated_ids.append(index)
            pattern = np.append(pattern, index)
            pattern = pattern[1:]

    return generated_ids


def _generate_notes_transformer_sync(
    model, seeds, n_vocab, num_notes=500, temperature=0.8, top_k=50, top_p=0.95, max_seq_len=512
):
    """Autoregressive generation with a Transformer model using KV cache."""
    start = np.random.randint(0, len(seeds))
    sequence = list(np.array(seeds[start], dtype=np.int64).flatten())
    seed_len = len(sequence)

    model.eval()
    with torch.no_grad():
        if hasattr(model, "generate_step"):
            # Prefill: run the full seed through the model to build KV cache
            input_seq = sequence[-max_seq_len:]
            input_tensor = torch.LongTensor([input_seq])
            logits = model(input_tensor)
            next_logits = logits[0, -1, :]
            index = sample_with_top_k_top_p(next_logits, temperature=temperature, top_k=top_k, top_p=top_p)
            sequence.append(index)

            # Build KV cache from prefill
            x = model.token_embedding(input_tensor)
            kv_caches = []
            for layer in model.layers:
                x, cache = layer(x)
                kv_caches.append(cache)

            # Incremental generation with KV cache
            pos = len(input_seq)
            for _ in range(num_notes - 1):
                token = torch.LongTensor([[sequence[-1]]])
                next_logits, kv_caches = model.generate_step(token, kv_caches, start_pos=pos)
                index = sample_with_top_k_top_p(next_logits[0], temperature=temperature, top_k=top_k, top_p=top_p)
                sequence.append(index)
                pos += 1

                # Reset cache if we exceed max_seq_len
                if pos >= max_seq_len:
                    input_seq = sequence[-max_seq_len:]
                    input_tensor = torch.LongTensor([input_seq])
                    x = model.token_embedding(input_tensor)
                    kv_caches = []
                    for layer in model.layers:
                        x, cache = layer(x)
                        kv_caches.append(cache)
                    pos = len(input_seq)
        else:
            # Fallback: full forward pass per token
            for _ in range(num_notes):
                input_seq = sequence[-max_seq_len:]
                input_tensor = torch.LongTensor([input_seq])
                logits = model(input_tensor)
                next_logits = logits[0, -1, :]
                index = sample_with_top_k_top_p(next_logits, temperature=temperature, top_k=top_k, top_p=top_p)
                sequence.append(index)

    return sequence[seed_len:]


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
):
    """Generate a new melody using the specified model.

    Returns:
        tuple: (midi_path, wav_path) paths to the generated files.
    """
    t0 = time.monotonic()

    if model_id not in models:
        logger.error(f"Invalid model ID: {model_id}")
        raise ValueError(f"Invalid model ID: {model_id}")

    bundle = models[model_id]
    logger.info(
        f"generate_melody start: model={model_id}, arch={bundle.architecture}, "
        f"notes={num_notes}, temp={temperature}, instrument={midi_program}"
    )

    if bundle.seeds is None:
        raise ValueError(f"No seed sequences available for model {model_id}")

    loop = asyncio.get_event_loop()
    generated_ids = None
    generated_notes = None

    if bundle.architecture == "transformer":
        max_seq_len = getattr(bundle.model, "max_seq_len", 512)

        effective_seeds = bundle.seeds
        if seed_midi and bundle.tokenizer:
            seq_length = len(bundle.seeds[0]) if bundle.seeds else max_seq_len
            seed_seq = await loop.run_in_executor(None, midi_to_seed_sequence, seed_midi, bundle.tokenizer, seq_length)
            effective_seeds = [seed_seq.tolist()]

        generated_ids = await loop.run_in_executor(
            None,
            _generate_notes_transformer_sync,
            bundle.model,
            effective_seeds,
            bundle.n_vocab,
            num_notes,
            temperature,
            top_k,
            top_p,
            max_seq_len,
        )
    elif bundle.tokenizer is not None:
        effective_seeds = bundle.seeds
        if seed_midi:
            seq_length = len(bundle.seeds[0]) if bundle.seeds else 100
            seed_seq = await loop.run_in_executor(None, midi_to_seed_sequence, seed_midi, bundle.tokenizer, seq_length)
            effective_seeds = [seed_seq.tolist()]

        generated_ids = await loop.run_in_executor(
            None,
            _generate_notes_remi_sync,
            bundle.model,
            effective_seeds,
            bundle.tokenizer,
            bundle.n_vocab,
            num_notes,
            temperature,
            top_k,
            top_p,
            bundle.model_version,
        )
    else:
        generated_notes = await loop.run_in_executor(
            None,
            _generate_notes_sync,
            bundle.model,
            bundle.seeds,
            bundle.pitchnames,
            bundle.n_vocab,
            num_notes,
            temperature,
            top_k,
            top_p,
            bundle.model_version,
        )

    inference_ms = round((time.monotonic() - t0) * 1000)
    logger.info(f"generate_melody inference done: model={model_id}, duration={inference_ms}ms")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    timestamp = uuid.uuid4().hex[:12]
    midi_file = os.path.join(output_dir, f"generated_melody_{timestamp}.mid")
    wav_file = os.path.join(output_dir, f"generated_melody_{timestamp}.wav")

    if bundle.tokenizer is not None:
        await loop.run_in_executor(
            None, create_midi_from_tokens, generated_ids, bundle.tokenizer, midi_file, midi_program
        )
    else:
        await loop.run_in_executor(None, create_midi_from_notes, generated_notes, midi_file, midi_program)

    if soundfont_path and os.path.exists(soundfont_path):
        await loop.run_in_executor(None, convert_midi_to_wav, midi_file, wav_file, soundfont_path)
    else:
        wav_file = None
        logger.warning("SoundFont not found, skipping WAV conversion")

    total_ms = round((time.monotonic() - t0) * 1000)
    logger.info(f"generate_melody complete: model={model_id}, total={total_ms}ms")

    return midi_file, wav_file


async def generate_melody_streaming(
    model_id,
    models,
    num_notes=500,
    temperature=0.8,
    top_k=50,
    top_p=0.95,
    midi_program=0,
):
    """Async generator that yields note events for WebSocket streaming."""
    logger.info(f"generate_melody_streaming start: model={model_id}, notes={num_notes}")
    if model_id not in models:
        raise ValueError(f"Invalid model ID: {model_id}")

    bundle = models[model_id]

    if bundle.seeds is None:
        raise ValueError(f"No seed sequences available for model {model_id}")

    if bundle.architecture == "transformer":
        max_seq_len = getattr(bundle.model, "max_seq_len", 512)
        start = np.random.randint(0, len(bundle.seeds))
        sequence = list(np.array(bundle.seeds[start], dtype=np.int64).flatten())
        seed_len = len(sequence)

        bundle.model.eval()
        offset = 0.0
        with torch.no_grad():
            use_kv_cache = hasattr(bundle.model, "generate_step")

            if use_kv_cache:
                # Prefill: build KV cache from seed sequence
                input_seq = sequence[-max_seq_len:]
                input_tensor = torch.LongTensor([input_seq])
                x = bundle.model.token_embedding(input_tensor)
                kv_caches = []
                for layer in bundle.model.layers:
                    x, cache = layer(x)
                    kv_caches.append(cache)

                logits = bundle.model(input_tensor)
                next_logits = logits[0, -1, :]
                index = sample_with_top_k_top_p(next_logits, temperature=temperature, top_k=top_k, top_p=top_p)
                sequence.append(index)
                pos = len(input_seq)

                note_event = token_to_note_event(index, bundle.tokenizer, 0, offset)
                if note_event:
                    offset = note_event.get("offset", offset) + note_event.get("duration", 0.5)
                    yield note_event

                # Incremental generation with KV cache
                for i in range(1, num_notes):
                    token = torch.LongTensor([[sequence[-1]]])
                    next_logits, kv_caches = bundle.model.generate_step(token, kv_caches, start_pos=pos)
                    index = sample_with_top_k_top_p(next_logits[0], temperature=temperature, top_k=top_k, top_p=top_p)
                    sequence.append(index)
                    pos += 1

                    if pos >= max_seq_len:
                        input_seq = sequence[-max_seq_len:]
                        input_tensor = torch.LongTensor([input_seq])
                        x = bundle.model.token_embedding(input_tensor)
                        kv_caches = []
                        for layer in bundle.model.layers:
                            x, cache = layer(x)
                            kv_caches.append(cache)
                        pos = len(input_seq)

                    note_event = token_to_note_event(index, bundle.tokenizer, i, offset)
                    if note_event:
                        offset = note_event.get("offset", offset) + note_event.get("duration", 0.5)
                        yield note_event

                    if i % 10 == 0:
                        await asyncio.sleep(0)
            else:
                # Fallback: full forward pass per token
                for i in range(num_notes):
                    input_seq = sequence[-max_seq_len:]
                    input_tensor = torch.LongTensor([input_seq])
                    logits = bundle.model(input_tensor)
                    next_logits = logits[0, -1, :]
                    index = sample_with_top_k_top_p(next_logits, temperature=temperature, top_k=top_k, top_p=top_p)
                    sequence.append(index)

                    note_event = token_to_note_event(index, bundle.tokenizer, i, offset)
                    if note_event:
                        offset = note_event.get("offset", offset) + note_event.get("duration", 0.5)
                        yield note_event

                    if i % 10 == 0:
                        await asyncio.sleep(0)

        yield {"type": "sequence_complete", "token_ids": sequence[seed_len:]}

    elif bundle.tokenizer is not None:
        start = np.random.randint(0, len(bundle.seeds))
        pattern = np.array(bundle.seeds[start], dtype=np.int64).flatten()
        generated_ids = []

        bundle.model.eval()
        offset = 0.0
        with torch.no_grad():
            for i in range(num_notes):
                input_tensor = torch.LongTensor(pattern).unsqueeze(0)
                logits = bundle.model(input_tensor)
                index = sample_with_top_k_top_p(logits[0], temperature=temperature, top_k=top_k, top_p=top_p)
                generated_ids.append(index)
                pattern = np.append(pattern, index)[1:]

                note_event = token_to_note_event(index, bundle.tokenizer, i, offset)
                if note_event:
                    offset = note_event.get("offset", offset) + note_event.get("duration", 0.5)
                    yield note_event

                if i % 10 == 0:
                    await asyncio.sleep(0)

        yield {"type": "sequence_complete", "token_ids": generated_ids}

    else:
        int_to_note = dict((number, note_name) for number, note_name in enumerate(bundle.pitchnames))
        start = np.random.randint(0, len(bundle.seeds))
        pattern = np.array(bundle.seeds[start])

        bundle.model.eval()
        offset = 0.0
        with torch.no_grad():
            for i in range(num_notes):
                if bundle.model_version >= 2:
                    if pattern.ndim == 2:
                        pattern_flat = pattern[:, 0].astype(np.int64)
                    else:
                        pattern_flat = pattern.astype(np.int64)
                    input_tensor = torch.LongTensor(pattern_flat).unsqueeze(0)
                else:
                    prediction_input = np.reshape(pattern, (1, len(pattern), 1))
                    prediction_input = prediction_input / float(bundle.n_vocab)
                    input_tensor = torch.FloatTensor(prediction_input)

                logits = bundle.model(input_tensor)
                index = sample_with_top_k_top_p(logits[0], temperature=temperature, top_k=top_k, top_p=top_p)

                result = int_to_note[index]
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

                if bundle.model_version >= 2:
                    pattern = np.append(pattern, index)
                    pattern = pattern[1:]
                else:
                    pattern = np.append(pattern, [[index]], axis=0)
                    pattern = pattern[1:]

                if i % 10 == 0:
                    await asyncio.sleep(0)

        yield {"type": "sequence_complete", "notes": [int_to_note[idx] for idx in range(len(bundle.pitchnames))]}
