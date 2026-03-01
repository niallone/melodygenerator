"""
Conditional generation support via prefix tokens.

Condition tokens are prepended to REMI sequences during training.
The model learns to attend to these prefix tokens via standard self-attention.

Condition token vocabulary (~45 tokens):
  - Key signature (25): Key_Cmaj, Key_Cmin, ..., Key_Bmaj, Key_Bmin, Key_none
  - Tempo (10 buckets): Tempo_60, ..., Tempo_200
  - Style (5): Style_classical, Style_dance, Style_jazz, Style_various, Style_none
  - Reserved (5): for future use
"""

# Key signatures
KEYS = [
    "Cmaj", "Cmin", "C#maj", "C#min", "Dmaj", "Dmin", "D#maj", "D#min",
    "Emaj", "Emin", "Fmaj", "Fmin", "F#maj", "F#min", "Gmaj", "Gmin",
    "G#maj", "G#min", "Amaj", "Amin", "A#maj", "A#min", "Bmaj", "Bmin",
    "none",
]

# Tempo buckets
TEMPO_BUCKETS = [60, 75, 90, 105, 120, 135, 150, 165, 180, 200]

# Styles
STYLES = ["classical", "dance", "jazz", "various", "none"]


def build_condition_vocab():
    """Build the condition token vocabulary.

    Returns:
        list: List of condition token strings, ordered deterministically.
    """
    tokens = []
    for key in KEYS:
        tokens.append(f"Key_{key}")
    for tempo in TEMPO_BUCKETS:
        tokens.append(f"Tempo_{tempo}")
    for style in STYLES:
        tokens.append(f"Style_{style}")
    # Reserved tokens
    for i in range(5):
        tokens.append(f"Reserved_{i}")
    return tokens


def get_n_conditions():
    """Return total number of condition tokens."""
    return len(build_condition_vocab())


def quantize_tempo(bpm):
    """Map a BPM value to the nearest tempo bucket."""
    if bpm is None:
        return None
    closest = min(TEMPO_BUCKETS, key=lambda t: abs(t - bpm))
    return closest


def extract_conditions_from_midi(midi_path, style_hint=None):
    """
    Extract condition tokens from a MIDI file.

    Args:
        midi_path: Path to MIDI file.
        style_hint: Optional style string (e.g., inferred from directory name).

    Returns:
        dict: {'key': str or None, 'tempo': int or None, 'style': str or None}
    """
    key = None
    tempo = None

    try:
        from music21 import converter
        midi = converter.parse(midi_path)

        # Extract key
        analyzed_key = midi.analyze('key')
        if analyzed_key:
            key_name = analyzed_key.tonic.name.replace('-', 'b')
            mode = 'maj' if analyzed_key.mode == 'major' else 'min'
            key = f"{key_name}{mode}"
    except Exception:
        pass

    try:
        from music21 import converter
        midi = converter.parse(midi_path)

        # Extract tempo
        tempo_marks = midi.flat.getElementsByClass('MetronomeMark')
        if tempo_marks:
            tempo = quantize_tempo(int(tempo_marks[0].number))
    except Exception:
        pass

    # Infer style from directory name if not provided
    style = style_hint
    if style and style not in STYLES:
        # Try to match partial names
        style_lower = style.lower()
        for s in STYLES:
            if s in style_lower:
                style = s
                break
        else:
            style = "various"

    return {'key': key, 'tempo': tempo, 'style': style}


def build_condition_prefix_ids(condition_token_map, key=None, tempo=None, style=None):
    """
    Build a list of condition token IDs to prepend to a sequence.

    Args:
        condition_token_map: Dict mapping condition token strings to IDs.
        key: Key signature string (e.g., "Cmaj") or None.
        tempo: Tempo bucket int (e.g., 120) or None.
        style: Style string (e.g., "classical") or None.

    Returns:
        list: List of token IDs for the condition prefix.
    """
    prefix = []

    if key:
        token = f"Key_{key}"
        if token in condition_token_map:
            prefix.append(condition_token_map[token])
        else:
            prefix.append(condition_token_map.get("Key_none", 0))
    else:
        prefix.append(condition_token_map.get("Key_none", 0))

    if tempo:
        token = f"Tempo_{quantize_tempo(tempo)}"
        if token in condition_token_map:
            prefix.append(condition_token_map[token])
    else:
        # Default to 120 BPM
        prefix.append(condition_token_map.get("Tempo_120", 0))

    if style:
        token = f"Style_{style}"
        if token in condition_token_map:
            prefix.append(condition_token_map[token])
        else:
            prefix.append(condition_token_map.get("Style_none", 0))
    else:
        prefix.append(condition_token_map.get("Style_none", 0))

    return prefix
