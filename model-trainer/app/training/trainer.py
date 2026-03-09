"""Unified trainer for both LSTM and Transformer architectures."""

import json
import os
import random

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from app.evaluation import compute_perplexity
from .scheduler import WarmupCosineScheduler


def set_seed(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class Trainer:
    """Architecture-agnostic trainer for melody generation models.

    Handles LSTM (next-token prediction) and Transformer (causal LM loss at all
    positions) with a single training loop. Architecture-specific differences are
    isolated to data preparation, scheduler creation, and checkpoint format.
    """

    def __init__(self, model, config, device=None):
        self.model = model
        self.config = config
        self.device = device or torch.device("cpu")
        self.model.to(self.device)
        self.is_transformer = config.architecture == "transformer"

    async def train(self, network_input, network_output, experiment_tracker=None):
        """Run the full training loop.

        Args:
            network_input: numpy array of input sequences.
            network_output: numpy array of target tokens.
            experiment_tracker: optional ExperimentTracker instance.
        """
        cfg = self.config
        set_seed(42)

        print(f"Training {cfg.architecture} | epochs={cfg.epochs} batch={cfg.batch_size}")
        param_count = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        print(f"Parameters: {param_count:,}")

        use_bf16 = self.is_transformer and self.device.type == "cuda"
        if use_bf16:
            print("Using BF16 mixed precision")

        # Prepare tensors (architecture-specific)
        x_all, y_all = self._prepare_tensors(network_input, network_output)

        # Train/val split
        train_loader, val_loader = self._create_dataloaders(x_all, y_all)

        # Optimizer + scheduler
        optimizer = torch.optim.AdamW(
            self.model.parameters(), lr=cfg.learning_rate, weight_decay=cfg.weight_decay
        )
        scheduler = self._create_scheduler(optimizer, len(train_loader))
        criterion = nn.CrossEntropyLoss()

        os.makedirs(cfg.output_dir, exist_ok=True)
        best_val_loss = float("inf")
        patience_counter = 0
        global_step = 0

        for epoch in range(cfg.epochs):
            # --- Training ---
            train_loss, global_step = self._train_epoch(
                train_loader, criterion, optimizer, scheduler,
                use_bf16, global_step,
            )

            # --- Validation ---
            val_loss = self._validate_epoch(val_loader, criterion, use_bf16)

            current_lr = optimizer.param_groups[0]["lr"]
            if not self.is_transformer:
                scheduler.step()

            perplexity = compute_perplexity(val_loss)
            print(
                f"Epoch {epoch + 1}/{cfg.epochs} - "
                f"Train: {train_loss:.4f} - Val: {val_loss:.4f} - "
                f"PPL: {perplexity:.2f} - LR: {current_lr:.6f}"
            )

            if experiment_tracker:
                experiment_tracker.log_epoch(epoch + 1, train_loss, val_loss, current_lr, perplexity)

            # --- Checkpointing + early stopping ---
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                ckpt_path = os.path.join(
                    cfg.output_dir,
                    f"weights-improvement-{epoch + 1:02d}-{val_loss:.4f}.pt",
                )
                self._save_checkpoint(ckpt_path)
                print(f"Checkpoint saved: {ckpt_path}")
            else:
                patience_counter += 1
                if patience_counter >= cfg.early_stopping_patience:
                    print(f"Early stopping after {epoch + 1} epochs (patience={cfg.early_stopping_patience})")
                    break

        print(f"Training complete. Best val loss: {best_val_loss:.4f}")

        # Save final model + metadata + seeds
        self._save_checkpoint(cfg.model_path)
        self._save_metadata(cfg)
        self._save_seeds(cfg, network_input)

        if experiment_tracker:
            experiment_tracker.log_model_summary(param_count, cfg.architecture)
            experiment_tracker.finish()

        print(f"Model saved to {cfg.model_path}")

    # ------------------------------------------------------------------
    # Architecture-specific data preparation
    # ------------------------------------------------------------------

    def _prepare_tensors(self, network_input, network_output):
        """Convert numpy arrays to tensors, handling architecture differences."""
        if self.is_transformer:
            # Transformer: causal LM loss at all positions
            # Concatenate input + output to get full sequences, then shift
            full_seqs = np.concatenate(
                [network_input, network_output.reshape(-1, 1)], axis=1
            )
            x = torch.LongTensor(full_seqs[:, :-1]).to(self.device)
            y = torch.LongTensor(full_seqs[:, 1:]).to(self.device)
        else:
            # LSTM: next-token prediction (single target per sequence)
            if network_input.dtype == np.int64:
                x = torch.LongTensor(network_input).to(self.device)
            else:
                x = torch.FloatTensor(network_input).to(self.device)
            y = torch.LongTensor(network_output).to(self.device)
        return x, y

    def _create_dataloaders(self, x_all, y_all):
        """Split data and create train/val DataLoaders."""
        n_samples = len(x_all)
        indices = np.random.permutation(n_samples)
        val_size = max(1, int(n_samples * self.config.validation_split))

        train_idx, val_idx = indices[val_size:], indices[:val_size]
        print(f"Train samples: {len(train_idx)}, Val samples: {len(val_idx)}")

        train_ds = TensorDataset(x_all[train_idx], y_all[train_idx])
        val_ds = TensorDataset(x_all[val_idx], y_all[val_idx])

        train_loader = DataLoader(train_ds, batch_size=self.config.batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=self.config.batch_size, shuffle=False)
        return train_loader, val_loader

    def _create_scheduler(self, optimizer, steps_per_epoch):
        """Create the appropriate LR scheduler."""
        cfg = self.config
        if self.is_transformer and cfg.warmup_steps > 0:
            total_steps = steps_per_epoch * cfg.epochs // cfg.accumulation_steps
            return WarmupCosineScheduler(optimizer, cfg.warmup_steps, total_steps)
        return torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=cfg.epochs)

    # ------------------------------------------------------------------
    # Training + validation loops
    # ------------------------------------------------------------------

    def _train_epoch(self, train_loader, criterion, optimizer, scheduler, use_bf16, global_step):
        """Run one training epoch. Returns (avg_loss, global_step)."""
        cfg = self.config
        self.model.train()
        total_loss = 0.0
        num_batches = 0

        if self.is_transformer:
            optimizer.zero_grad()

        for batch_idx, (batch_x, batch_y) in enumerate(train_loader):
            if self.is_transformer:
                loss = self._transformer_step(batch_x, batch_y, criterion, use_bf16)
                loss = loss / cfg.accumulation_steps
                loss.backward()

                if (batch_idx + 1) % cfg.accumulation_steps == 0:
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=cfg.grad_clip_max_norm)
                    optimizer.step()
                    scheduler.step()
                    optimizer.zero_grad()
                    global_step += 1

                total_loss += loss.item() * cfg.accumulation_steps
            else:
                optimizer.zero_grad()
                outputs = self.model(batch_x)
                loss = criterion(outputs, batch_y)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=cfg.grad_clip_max_norm)
                optimizer.step()
                total_loss += loss.item()

            num_batches += 1

        # Handle remaining gradients from incomplete accumulation batch
        if self.is_transformer:
            total_batches = batch_idx + 1
            if total_batches % cfg.accumulation_steps != 0:
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=cfg.grad_clip_max_norm)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()

        return total_loss / num_batches, global_step

    def _validate_epoch(self, val_loader, criterion, use_bf16):
        """Run one validation epoch. Returns avg_loss."""
        self.model.eval()
        total_loss = 0.0
        num_batches = 0

        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                if self.is_transformer:
                    loss = self._transformer_step(batch_x, batch_y, criterion, use_bf16)
                else:
                    outputs = self.model(batch_x)
                    loss = criterion(outputs, batch_y)
                total_loss += loss.item()
                num_batches += 1

        return total_loss / num_batches

    def _transformer_step(self, batch_x, batch_y, criterion, use_bf16):
        """Forward pass for Transformer with optional BF16."""
        with torch.amp.autocast("cuda", dtype=torch.bfloat16, enabled=use_bf16):
            logits = self.model(batch_x)
            return criterion(logits.reshape(-1, logits.size(-1)), batch_y.reshape(-1))

    # ------------------------------------------------------------------
    # Saving
    # ------------------------------------------------------------------

    def _save_checkpoint(self, path: str):
        """Save model checkpoint in the appropriate format."""
        if self.is_transformer:
            checkpoint = {
                "architecture": "transformer",
                "model_state_dict": self.model.state_dict(),
                "n_vocab": self.model.n_vocab,
                "model_version": 7,
                "config": {
                    "n_vocab": self.model.n_vocab,
                    "d_model": self.model.d_model,
                    "n_heads": self.model.n_heads,
                    "n_layers": self.model.n_layers,
                    "d_ff": self.model.d_ff,
                    "max_seq_len": self.model.max_seq_len,
                    "dropout": self.model.dropout_rate,
                },
            }
        else:
            checkpoint = {
                "model_state_dict": self.model.state_dict(),
                "n_vocab": self.model.n_vocab,
                "lstm_units": self.model.lstm_units,
                "dense_units": self.model.dense_units,
            }
            if hasattr(self.model, "embedding_dim"):
                checkpoint["embedding_dim"] = self.model.embedding_dim
            if hasattr(self.model, "model_version"):
                checkpoint["model_version"] = self.model.model_version
            if hasattr(self.model, "use_attention"):
                checkpoint["use_attention"] = self.model.use_attention
                checkpoint["num_attention_heads"] = getattr(self.model, "num_attention_heads", 4)
        torch.save(checkpoint, path)

    def _save_metadata(self, config):
        """Save training metadata as JSON."""
        metadata = {
            "n_vocab": self.model.n_vocab if hasattr(self.model, "n_vocab") else None,
            "architecture": config.architecture,
            "pitchnames": getattr(self, "_pitchnames", None),
            "note_to_int": getattr(self, "_note_to_int", None),
        }
        if config.tokenizer == "remi":
            metadata["tokenizer_type"] = "REMI"
            metadata["tokenizer_path"] = f"{config.name}_tokenizer"

        with open(config.metadata_path, "w") as f:
            json.dump(metadata, f)
        print(f"Metadata saved to {config.metadata_path}")

    def _save_seeds(self, config, network_input):
        """Save random seed sequences for generation."""
        num_seeds = min(100, len(network_input))
        seed_indices = np.random.choice(len(network_input), num_seeds, replace=False)
        seeds = network_input[seed_indices].tolist()
        with open(config.seeds_path, "w") as f:
            json.dump(seeds, f)
        print(f"Seeds saved to {config.seeds_path}")
