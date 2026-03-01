import os
import json
import math
import random
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset


def set_seed(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class ModelTrainer:
    """
    A class for training the PyTorch LSTM model.
    """

    def __init__(self, model, device=None):
        self.model = model
        self.device = device or torch.device('cpu')
        self.model.to(self.device)

    async def train(self, network_input, network_output, model_path, epochs=50,
                    batch_size=64, pitchnames=None, note_to_int=None,
                    learning_rate=1e-3, weight_decay=0.01, grad_clip_max_norm=1.0,
                    validation_split=0.1, early_stopping_patience=10):
        """
        Train the neural network model.

        Args:
            network_input (numpy.ndarray): Input data for training.
            network_output (numpy.ndarray): Target output data (integer class indices).
            model_path (str): Path where the trained model should be saved.
            epochs (int): Number of training epochs.
            batch_size (int): Batch size for training.
            pitchnames (list): List of unique pitch names.
            note_to_int (dict): Mapping from note names to integers.
            learning_rate (float): Learning rate for optimizer.
            weight_decay (float): Weight decay for AdamW.
            grad_clip_max_norm (float): Max norm for gradient clipping.
            validation_split (float): Fraction of data for validation.
            early_stopping_patience (int): Epochs to wait before early stopping.
        """
        print(f"Training model with {epochs} epochs and batch size {batch_size}...")
        set_seed(42)

        # Convert numpy arrays to PyTorch tensors
        if network_input.dtype == np.int64:
            x_all = torch.LongTensor(network_input).to(self.device)
        else:
            x_all = torch.FloatTensor(network_input).to(self.device)
        y_all = torch.LongTensor(network_output).to(self.device)

        # Train/val split
        n_samples = len(x_all)
        indices = np.random.permutation(n_samples)
        val_size = max(1, int(n_samples * validation_split))
        val_indices = indices[:val_size]
        train_indices = indices[val_size:]

        x_train, y_train = x_all[train_indices], y_all[train_indices]
        x_val, y_val = x_all[val_indices], y_all[val_indices]

        train_dataset = TensorDataset(x_train, y_train)
        val_dataset = TensorDataset(x_val, y_val)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

        print(f"Train samples: {len(train_indices)}, Val samples: {len(val_indices)}")

        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.AdamW(
            self.model.parameters(), lr=learning_rate, weight_decay=weight_decay
        )
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

        best_val_loss = float('inf')
        patience_counter = 0
        checkpoint_dir = os.path.dirname(model_path)

        for epoch in range(epochs):
            # Training phase
            self.model.train()
            train_loss = 0.0
            train_batches = 0
            for batch_x, batch_y in train_loader:
                optimizer.zero_grad()
                outputs = self.model(batch_x)
                loss = criterion(outputs, batch_y)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=grad_clip_max_norm)
                optimizer.step()
                train_loss += loss.item()
                train_batches += 1

            avg_train_loss = train_loss / train_batches

            # Validation phase
            self.model.eval()
            val_loss = 0.0
            val_batches = 0
            with torch.no_grad():
                for batch_x, batch_y in val_loader:
                    outputs = self.model(batch_x)
                    loss = criterion(outputs, batch_y)
                    val_loss += loss.item()
                    val_batches += 1

            avg_val_loss = val_loss / val_batches
            current_lr = scheduler.get_last_lr()[0]
            scheduler.step()

            print(f"Epoch {epoch + 1}/{epochs} - Train: {avg_train_loss:.4f} - Val: {avg_val_loss:.4f} - LR: {current_lr:.6f}")

            # Save best model by validation loss
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                patience_counter = 0
                checkpoint_path = os.path.join(
                    checkpoint_dir,
                    f"weights-improvement-{epoch + 1:02d}-{avg_val_loss:.4f}.pt"
                )
                self._save_checkpoint(checkpoint_path)
                print(f"Checkpoint saved: {checkpoint_path}")
            else:
                patience_counter += 1
                if patience_counter >= early_stopping_patience:
                    print(f"Early stopping triggered after {epoch + 1} epochs (patience={early_stopping_patience})")
                    break

        print(f"Model training completed. Best val loss: {best_val_loss:.4f}")

        # Save the final trained model
        self._save_checkpoint(model_path)
        print(f"Model saved to {model_path}")

        # Save metadata as JSON
        metadata_path = os.path.splitext(model_path)[0] + '_metadata.json'
        metadata = {
            'pitchnames': pitchnames,
            'note_to_int': note_to_int,
            'n_vocab': len(pitchnames) if pitchnames else self.model.n_vocab,
        }
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        print(f"Metadata saved to {metadata_path}")

        # Save seed sequences
        seeds_path = os.path.splitext(model_path)[0] + '_seeds.json'
        num_seeds = min(100, len(network_input))
        seed_indices = np.random.choice(len(network_input), num_seeds, replace=False)
        seeds = network_input[seed_indices].tolist()
        with open(seeds_path, 'w') as f:
            json.dump(seeds, f)
        print(f"Seeds saved to {seeds_path}")

    def _save_checkpoint(self, path):
        """Save model checkpoint with all necessary metadata."""
        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'n_vocab': self.model.n_vocab,
            'lstm_units': self.model.lstm_units,
            'dense_units': self.model.dense_units,
        }
        # Save embedding_dim if present
        if hasattr(self.model, 'embedding_dim'):
            checkpoint['embedding_dim'] = self.model.embedding_dim
        # Save model_version if present
        if hasattr(self.model, 'model_version'):
            checkpoint['model_version'] = self.model.model_version
        # Save attention params if present
        if hasattr(self.model, 'use_attention'):
            checkpoint['use_attention'] = self.model.use_attention
            checkpoint['num_attention_heads'] = getattr(self.model, 'num_attention_heads', 4)
        torch.save(checkpoint, path)


class _WarmupCosineScheduler(torch.optim.lr_scheduler._LRScheduler):
    """Linear warmup then cosine decay."""

    def __init__(self, optimizer, warmup_steps, total_steps, last_epoch=-1):
        self.warmup_steps = warmup_steps
        self.total_steps = total_steps
        super().__init__(optimizer, last_epoch)

    def get_lr(self):
        step = self.last_epoch
        if step < self.warmup_steps:
            scale = step / max(1, self.warmup_steps)
        else:
            progress = (step - self.warmup_steps) / max(1, self.total_steps - self.warmup_steps)
            scale = 0.5 * (1.0 + math.cos(math.pi * progress))
        return [base_lr * scale for base_lr in self.base_lrs]


class TransformerTrainer:
    """
    Trainer for MusicTransformer with causal LM loss at all positions,
    linear warmup + cosine decay, and gradient accumulation.
    """

    def __init__(self, model, device=None):
        self.model = model
        self.device = device or torch.device('cpu')
        self.model.to(self.device)

    async def train(self, network_input, network_output, model_path, epochs=50,
                    batch_size=32, n_vocab=None, learning_rate=1e-3, weight_decay=0.01,
                    grad_clip_max_norm=1.0, validation_split=0.1,
                    early_stopping_patience=10, warmup_steps=1000,
                    accumulation_steps=2):
        """
        Train the Transformer with causal LM loss.

        For Transformer training, network_input contains sequences of length seq_len,
        and we compute loss at ALL positions (shifted by 1).
        """
        print(f"Training Transformer with {epochs} epochs, batch={batch_size}, accum={accumulation_steps}")
        set_seed(42)
        print(f"Model parameters: {self.model.count_parameters():,}")

        use_bf16 = self.device.type == 'cuda'
        if use_bf16:
            print("Using BF16 mixed precision")

        # Build contiguous chunks: input = tokens[:-1], target = tokens[1:]
        # network_input shape: (n_seqs, seq_len), network_output: (n_seqs,) — last token
        # Concatenate input + output to get full sequences of seq_len+1
        full_seqs = np.concatenate([
            network_input,
            network_output.reshape(-1, 1)
        ], axis=1)  # (n_seqs, seq_len+1)

        x_all = torch.LongTensor(full_seqs[:, :-1]).to(self.device)
        y_all = torch.LongTensor(full_seqs[:, 1:]).to(self.device)

        # Train/val split
        n_samples = len(x_all)
        indices = np.random.permutation(n_samples)
        val_size = max(1, int(n_samples * validation_split))
        val_indices = indices[:val_size]
        train_indices = indices[val_size:]

        train_dataset = TensorDataset(x_all[train_indices], y_all[train_indices])
        val_dataset = TensorDataset(x_all[val_indices], y_all[val_indices])
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

        print(f"Train samples: {len(train_indices)}, Val samples: {len(val_indices)}")

        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.AdamW(
            self.model.parameters(), lr=learning_rate, weight_decay=weight_decay
        )

        total_steps = len(train_loader) * epochs // accumulation_steps
        scheduler = _WarmupCosineScheduler(optimizer, warmup_steps, total_steps)

        best_val_loss = float('inf')
        patience_counter = 0
        checkpoint_dir = os.path.dirname(model_path)
        global_step = 0

        for epoch in range(epochs):
            self.model.train()
            train_loss = 0.0
            train_batches = 0
            optimizer.zero_grad()

            for batch_idx, (batch_x, batch_y) in enumerate(train_loader):
                # batch_x: (batch, seq_len), batch_y: (batch, seq_len)
                with torch.amp.autocast('cuda', dtype=torch.bfloat16, enabled=use_bf16):
                    logits = self.model(batch_x)  # (batch, seq_len, n_vocab)
                    # Flatten for cross-entropy: (batch*seq_len, n_vocab) vs (batch*seq_len,)
                    loss = criterion(
                        logits.reshape(-1, logits.size(-1)),
                        batch_y.reshape(-1)
                    )
                loss = loss / accumulation_steps
                loss.backward()

                if (batch_idx + 1) % accumulation_steps == 0:
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(), max_norm=grad_clip_max_norm
                    )
                    optimizer.step()
                    scheduler.step()
                    optimizer.zero_grad()
                    global_step += 1

                train_loss += loss.item() * accumulation_steps
                train_batches += 1

            # Handle remaining gradients from incomplete accumulation batch
            total_batches = batch_idx + 1
            if total_batches % accumulation_steps != 0:
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(), max_norm=grad_clip_max_norm
                )
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()

            avg_train_loss = train_loss / train_batches

            # Validation
            self.model.eval()
            val_loss = 0.0
            val_batches = 0
            with torch.no_grad():
                for batch_x, batch_y in val_loader:
                    with torch.amp.autocast('cuda', dtype=torch.bfloat16, enabled=use_bf16):
                        logits = self.model(batch_x)
                        loss = criterion(
                            logits.reshape(-1, logits.size(-1)),
                            batch_y.reshape(-1)
                        )
                    val_loss += loss.item()
                    val_batches += 1

            avg_val_loss = val_loss / val_batches
            current_lr = optimizer.param_groups[0]['lr']

            print(f"Epoch {epoch + 1}/{epochs} - Train: {avg_train_loss:.4f} - Val: {avg_val_loss:.4f} - LR: {current_lr:.6f}")

            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                patience_counter = 0
                checkpoint_path = os.path.join(
                    checkpoint_dir,
                    f"weights-improvement-{epoch + 1:02d}-{avg_val_loss:.4f}.pt"
                )
                self._save_checkpoint(checkpoint_path)
                print(f"Checkpoint saved: {checkpoint_path}")
            else:
                patience_counter += 1
                if patience_counter >= early_stopping_patience:
                    print(f"Early stopping after {epoch + 1} epochs")
                    break

        print(f"Training completed. Best val loss: {best_val_loss:.4f}")

        # Save final model
        self._save_checkpoint(model_path)
        print(f"Model saved to {model_path}")

        # Save metadata
        metadata_path = os.path.splitext(model_path)[0] + '_metadata.json'
        metadata = {
            'pitchnames': None,
            'note_to_int': None,
            'n_vocab': n_vocab or self.model.n_vocab,
        }
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)

        # Save seeds
        seeds_path = os.path.splitext(model_path)[0] + '_seeds.json'
        num_seeds = min(100, len(network_input))
        seed_indices = np.random.choice(len(network_input), num_seeds, replace=False)
        seeds = network_input[seed_indices].tolist()
        with open(seeds_path, 'w') as f:
            json.dump(seeds, f)
        print(f"Seeds saved to {seeds_path}")

    def _save_checkpoint(self, path):
        """Save Transformer checkpoint."""
        checkpoint = {
            'architecture': 'transformer',
            'model_state_dict': self.model.state_dict(),
            'n_vocab': self.model.n_vocab,
            'model_version': 7,
            'config': {
                'n_vocab': self.model.n_vocab,
                'd_model': self.model.d_model,
                'n_heads': self.model.n_heads,
                'n_layers': self.model.n_layers,
                'd_ff': self.model.d_ff,
                'max_seq_len': self.model.max_seq_len,
                'dropout': self.model.dropout_rate,
            },
        }
        torch.save(checkpoint, path)
