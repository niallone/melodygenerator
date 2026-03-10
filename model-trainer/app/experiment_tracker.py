import json
import math
import os


class ExperimentTracker:
    """Thin wrapper around Weights & Biases for experiment tracking."""

    def __init__(self, project: str, config: dict, run_name: str | None = None, enabled: bool = True):
        self._enabled = enabled
        self._run = None
        self._config = config

        if not enabled:
            return

        try:
            import wandb
            self._run = wandb.init(project=project, name=run_name, config=config)
        except ImportError:
            print("wandb not installed — tracking disabled")
            self._enabled = False
        except Exception as e:
            print(f"wandb init failed — tracking disabled: {e}")
            self._enabled = False

    def log_epoch(self, epoch: int, train_loss: float, val_loss: float, lr: float, perplexity: float | None = None):
        if not self._enabled:
            return
        import wandb
        metrics = {
            "epoch": epoch,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "learning_rate": lr,
        }
        if perplexity is not None:
            metrics["perplexity"] = perplexity
        wandb.log(metrics, step=epoch)

    def log_batch(self, step: int, loss: float, grad_norm: float):
        """Log per-batch metrics (loss, gradient norm)."""
        if not self._enabled:
            return
        import wandb
        wandb.log({"batch/loss": loss, "batch/grad_norm": grad_norm}, step=step)

    def log_model_summary(self, param_count: int, architecture: str):
        if not self._enabled:
            return
        import wandb
        wandb.log({"param_count": param_count, "architecture": architecture})

    def log_evaluation(self, metrics: dict):
        if not self._enabled:
            return
        import wandb
        wandb.log({"eval/" + k: v for k, v in metrics.items()})

    def save_config_locally(self, output_dir: str):
        """Save a local copy of the training config for reproducibility."""
        path = os.path.join(output_dir, "train_config.json")
        with open(path, "w") as f:
            json.dump(self._config, f, indent=2)
        print(f"Config saved to {path}")

    def finish(self):
        if not self._enabled or self._run is None:
            return
        self._run.finish()
