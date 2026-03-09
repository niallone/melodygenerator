import gzip
import math
from collections import Counter


def compute_perplexity(loss: float) -> float:
    """Compute perplexity from cross-entropy loss."""
    return math.exp(loss)


def compute_repetition_scores(tokens: list[int]) -> dict:
    """Compute n-gram repetition ratios and compression ratio for a token sequence."""
    results = {}

    for n in (4, 8):
        if len(tokens) < n:
            results[f"{n}gram_repetition"] = 0.0
            continue
        ngrams = [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]
        counts = Counter(ngrams)
        repeated = sum(1 for c in counts.values() if c > 1)
        results[f"{n}gram_repetition"] = repeated / len(counts) if counts else 0.0

    # Compression ratio: lower = more repetitive
    raw = bytes(t % 256 for t in tokens)
    compressed = gzip.compress(raw)
    results["compression_ratio"] = len(compressed) / len(raw) if raw else 1.0

    return results


def analyze_pitch_distribution(tokens: list[int], tokenizer=None) -> dict:
    """Analyze pitch distribution from a token sequence.

    If tokenizer is provided, attempts to decode tokens to MIDI pitches.
    Otherwise treats tokens directly as MIDI pitch values.
    """
    pitches = []

    if tokenizer is not None:
        try:
            # MidiTok: decode tokens to get note events
            midi = tokenizer.decode([tokens])
            for track in midi.tracks:
                for note in track.notes:
                    pitches.append(note.pitch)
        except Exception:
            # Fall back to treating tokens as pitches
            pitches = [t for t in tokens if 21 <= t <= 108]
    else:
        pitches = [t for t in tokens if 21 <= t <= 108]

    if not pitches:
        return {"pitch_class_histogram": [0] * 12, "mean_pitch": 0, "pitch_range": 0, "intervals": {}}

    # Pitch class histogram (C=0 through B=11)
    histogram = [0] * 12
    for p in pitches:
        histogram[p % 12] += 1
    total = sum(histogram)
    histogram = [h / total for h in histogram] if total else histogram

    # Interval distribution
    intervals = [pitches[i + 1] - pitches[i] for i in range(len(pitches) - 1)]
    interval_counts = Counter(intervals)
    top_intervals = dict(interval_counts.most_common(10))

    return {
        "pitch_class_histogram": histogram,
        "mean_pitch": sum(pitches) / len(pitches),
        "pitch_range": max(pitches) - min(pitches),
        "num_unique_pitches": len(set(pitches)),
        "top_intervals": top_intervals,
    }


def evaluate_generation(tokens: list[int], tokenizer=None) -> dict:
    """Run all evaluation metrics on a generated token sequence."""
    results = {}
    results.update(compute_repetition_scores(tokens))
    results.update(analyze_pitch_distribution(tokens, tokenizer))
    return results
