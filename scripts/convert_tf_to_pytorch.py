"""
One-time conversion script: TensorFlow .h5 + .pkl models → PyTorch .pt + JSON metadata.

Reads weights directly from .h5 files using h5py (no TensorFlow required).

Usage:
    python scripts/convert_tf_to_pytorch.py
"""

import os
import sys
import pickle
import json
import numpy as np
import h5py

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'model-trainer', 'app'))

import torch
from model_builder import MelodyLSTM


def extract_weights_from_h5(h5_path):
    """
    Extract layer weights and architecture from an .h5 file.

    Returns:
        tuple: (lstm_weights, dense_weights, lstm_units)
            lstm_weights: list of (kernel, recurrent_kernel, bias) per LSTM layer
            dense_weights: list of (kernel, bias) per Dense layer
            lstm_units: list of hidden sizes per LSTM layer
    """
    lstm_weights = []
    dense_weights = []
    lstm_units = []

    with h5py.File(h5_path, 'r') as f:
        # Parse model config for layer names and units
        model_config = f.attrs.get('model_config')
        if isinstance(model_config, bytes):
            model_config = model_config.decode('utf-8')
        config = json.loads(model_config)

        weight_root = f['model_weights']

        for layer_config in config['config']['layers']:
            class_name = layer_config['class_name']
            layer_name = layer_config['config']['name']

            if class_name == 'LSTM':
                units = layer_config['config']['units']
                lstm_units.append(units)

                # Navigate: model_weights/<layer>/<layer>/lstm_cell*/
                layer_group = weight_root[layer_name][layer_name]
                # Find the lstm_cell subgroup (may be lstm_cell, lstm_cell_1, etc.)
                cell_key = [k for k in layer_group.keys() if k.startswith('lstm_cell')][0]
                cell_group = layer_group[cell_key]

                kernel = np.array(cell_group['kernel:0'])
                recurrent_kernel = np.array(cell_group['recurrent_kernel:0'])
                bias = np.array(cell_group['bias:0'])
                lstm_weights.append((kernel, recurrent_kernel, bias))

            elif class_name == 'Dense':
                # Navigate: model_weights/<layer>/<layer>/
                layer_group = weight_root[layer_name][layer_name]
                kernel = np.array(layer_group['kernel:0'])
                bias = np.array(layer_group['bias:0'])
                dense_weights.append((kernel, bias))

    return lstm_weights, dense_weights, lstm_units


def convert_model(h5_path, pkl_path, output_dir):
    """Convert a single TF model + pkl metadata to PyTorch format."""
    print(f"  Loading weights from: {h5_path}")
    lstm_weights, dense_weights, lstm_units = extract_weights_from_h5(h5_path)

    print(f"  Architecture: LSTM units={lstm_units}")
    for i, (k, rk, b) in enumerate(lstm_weights):
        print(f"    LSTM {i}: kernel={k.shape}, recurrent_kernel={rk.shape}, bias={b.shape}")
    for i, (k, b) in enumerate(dense_weights):
        print(f"    Dense {i}: kernel={k.shape}, bias={b.shape}")

    print(f"  Loading pickle data: {pkl_path}")
    with open(pkl_path, 'rb') as f:
        network_input, pitchnames, note_to_int, n_vocab = pickle.load(f)

    if isinstance(n_vocab, dict):
        n_vocab = len(pitchnames)
    elif not isinstance(n_vocab, (int, float)):
        n_vocab = len(pitchnames)
    n_vocab = int(n_vocab)

    dense_units = dense_weights[0][0].shape[1] if dense_weights else 256
    print(f"  n_vocab: {n_vocab}, dense_units: {dense_units}")

    # Create PyTorch model with matching architecture
    pt_model = MelodyLSTM(n_vocab, lstm_units=lstm_units, dense_units=dense_units)
    state_dict = pt_model.state_dict()

    # Map LSTM weights
    for i, (kernel, recurrent_kernel, bias) in enumerate(lstm_weights):
        # TF: kernel [input_size, 4*hidden] → PT: weight_ih [4*hidden, input_size]
        state_dict[f'lstm_layers.{i}.weight_ih_l0'] = torch.FloatTensor(kernel.T)
        # TF: recurrent_kernel [hidden, 4*hidden] → PT: weight_hh [4*hidden, hidden]
        state_dict[f'lstm_layers.{i}.weight_hh_l0'] = torch.FloatTensor(recurrent_kernel.T)
        # Bias: put full bias in bias_ih, zeros in bias_hh
        state_dict[f'lstm_layers.{i}.bias_ih_l0'] = torch.FloatTensor(bias)
        state_dict[f'lstm_layers.{i}.bias_hh_l0'] = torch.zeros(bias.shape[0])

    # Map Dense weights
    if len(dense_weights) >= 1:
        state_dict['fc1.weight'] = torch.FloatTensor(dense_weights[0][0].T)
        state_dict['fc1.bias'] = torch.FloatTensor(dense_weights[0][1])

    if len(dense_weights) >= 2:
        state_dict['fc2.weight'] = torch.FloatTensor(dense_weights[1][0].T)
        state_dict['fc2.bias'] = torch.FloatTensor(dense_weights[1][1])

    # Load weights
    pt_model.load_state_dict(state_dict)

    # Derive output file names
    base_name = os.path.splitext(os.path.basename(h5_path))[0]
    pt_path = os.path.join(output_dir, f"{base_name}.pt")
    metadata_path = os.path.join(output_dir, f"{base_name}_metadata.json")
    seeds_path = os.path.join(output_dir, f"{base_name}_seeds.json")

    # Save PyTorch model
    torch.save({
        'model_state_dict': pt_model.state_dict(),
        'n_vocab': n_vocab,
        'lstm_units': lstm_units,
        'dense_units': dense_units,
    }, pt_path)
    print(f"  Saved: {pt_path} ({os.path.getsize(pt_path) / 1024 / 1024:.1f} MB)")

    # Save metadata as JSON
    metadata = {
        'pitchnames': list(pitchnames) if not isinstance(pitchnames, list) else pitchnames,
        'note_to_int': note_to_int if isinstance(note_to_int, dict) else dict(note_to_int),
        'n_vocab': n_vocab,
    }
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f)
    print(f"  Saved: {metadata_path}")

    # Save seed sequences
    num_seeds = min(100, len(network_input))
    seed_indices = np.random.choice(len(network_input), num_seeds, replace=False)
    seeds = network_input[seed_indices].tolist()
    with open(seeds_path, 'w') as f:
        json.dump(seeds, f)
    print(f"  Saved: {seeds_path}")

    # Quick validation: forward pass
    print(f"  Validating forward pass...")
    pt_model.eval()
    sample = network_input[0:1] / float(n_vocab)
    with torch.no_grad():
        input_tensor = torch.FloatTensor(sample)
        logits = pt_model(input_tensor)
        probs = torch.softmax(logits, dim=-1)
        top5 = torch.topk(probs[0], 5)
        print(f"  Top-5: indices={top5.indices.tolist()}, probs={[f'{p:.4f}' for p in top5.values.tolist()]}")

    return pt_path, metadata_path, seeds_path


def main():
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))
    print(f"Models directory: {models_dir}")

    h5_files = sorted([f for f in os.listdir(models_dir) if f.endswith('.h5')])
    print(f"Found {len(h5_files)} model files: {h5_files}")

    results = []
    for h5_file in h5_files:
        h5_path = os.path.join(models_dir, h5_file)
        pkl_path = f"{h5_path}_data.pkl"

        if not os.path.exists(pkl_path):
            print(f"\nSkipping {h5_file}: no matching .pkl file found")
            results.append((h5_file, "SKIPPED (no pkl)"))
            continue

        print(f"\nConverting {h5_file}...")
        try:
            convert_model(h5_path, pkl_path, models_dir)
            results.append((h5_file, "OK"))
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((h5_file, f"ERROR: {str(e)}"))

    print("\n" + "=" * 60)
    print("CONVERSION SUMMARY")
    print("=" * 60)
    for model_name, status in results:
        print(f"  {model_name}: {status}")


if __name__ == '__main__':
    main()
