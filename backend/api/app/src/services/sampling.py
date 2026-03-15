"""Token sampling strategies: temperature, top-k, top-p (nucleus)."""

import numpy as np
import torch


def sample_with_top_k_top_p(logits, temperature=1.0, top_k=0, top_p=1.0):
    """Sample from logits with temperature, top-k, and top-p (nucleus) filtering.

    Args:
        logits: 1D tensor of raw logits.
        temperature: Temperature scaling factor.
        top_k: If > 0, keep only top-k logits.
        top_p: If < 1.0, keep smallest set of tokens with cumulative prob >= top_p.

    Returns:
        int: Sampled token index.
    """
    logits = logits.clone() / temperature

    # Track top-k indices before filtering for fallback
    top_k_indices = None
    if top_k > 0:
        top_k = min(top_k, logits.size(-1))
        values, top_k_indices = torch.topk(logits, top_k)
        min_val = values[-1]
        logits = torch.where(logits < min_val, torch.tensor(float("-inf")), logits)

    # Top-p (nucleus) filtering
    if top_p < 1.0:
        sorted_logits, sorted_indices = torch.sort(logits, descending=True)
        cumulative_probs = torch.cumsum(torch.softmax(sorted_logits, dim=-1), dim=-1)
        sorted_indices_to_remove = cumulative_probs > top_p
        sorted_indices_to_remove[1:] = sorted_indices_to_remove[:-1].clone()
        sorted_indices_to_remove[0] = False
        indices_to_remove = sorted_indices[sorted_indices_to_remove]
        logits[indices_to_remove] = float("-inf")

    # Handle case where all logits are -inf after filtering
    if torch.all(logits == float("-inf")):
        if top_k_indices is not None:
            return int(top_k_indices[np.random.randint(0, len(top_k_indices))].item())
        return int(np.random.randint(0, logits.size(-1)))

    probabilities = torch.softmax(logits, dim=-1).numpy()
    return int(np.random.choice(len(probabilities), p=probabilities))
