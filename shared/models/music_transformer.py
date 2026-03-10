import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class RMSNorm(nn.Module):
    """Root Mean Square Layer Normalization (no bias, no mean centering)."""

    def __init__(self, d_model, eps=1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(d_model))
        self.eps = eps

    def forward(self, x):
        norm = torch.rsqrt(x.float().pow(2).mean(-1, keepdim=True) + self.eps)
        return (x.float() * norm).type_as(x) * self.weight


class RotaryPositionEmbedding(nn.Module):
    """Rotary Position Embedding (RoPE) with auto-extending cache."""

    def __init__(self, d_head, max_seq_len=2048, base=10000.0):
        super().__init__()
        self.d_head = d_head
        self.base = base
        inv_freq = 1.0 / (base ** (torch.arange(0, d_head, 2).float() / d_head))
        self.register_buffer('inv_freq', inv_freq, persistent=True)
        self._build_cache(max_seq_len)

    def _build_cache(self, seq_len):
        t = torch.arange(seq_len, device=self.inv_freq.device, dtype=self.inv_freq.dtype)
        freqs = torch.outer(t, self.inv_freq)
        emb = torch.cat([freqs, freqs], dim=-1)
        self.register_buffer('cos_cached', emb.cos(), persistent=False)
        self.register_buffer('sin_cached', emb.sin(), persistent=False)
        self._cached_seq_len = seq_len

    def forward(self, seq_len):
        if seq_len > self._cached_seq_len:
            self._build_cache(seq_len)
        return self.cos_cached[:seq_len], self.sin_cached[:seq_len]


def _rotate_half(x):
    """Rotate half the hidden dimensions of x for RoPE."""
    x1 = x[..., :x.shape[-1] // 2]
    x2 = x[..., x.shape[-1] // 2:]
    return torch.cat([-x2, x1], dim=-1)


def apply_rotary_pos_emb(q, k, cos, sin):
    """Apply rotary positional embedding to query and key tensors."""
    # cos, sin: (seq_len, d_head) -> (1, 1, seq_len, d_head)
    cos = cos.unsqueeze(0).unsqueeze(0)
    sin = sin.unsqueeze(0).unsqueeze(0)
    q_embed = (q * cos) + (_rotate_half(q) * sin)
    k_embed = (k * cos) + (_rotate_half(k) * sin)
    return q_embed, k_embed


class RoPEMultiHeadAttention(nn.Module):
    """Multi-head attention with Rotary Position Embedding."""

    def __init__(self, d_model, n_heads, dropout=0.1, max_seq_len=2048):
        super().__init__()
        assert d_model % n_heads == 0

        self.d_model = d_model
        self.n_heads = n_heads
        self.d_head = d_model // n_heads

        self.qkv_proj = nn.Linear(d_model, 3 * d_model, bias=False)
        self.out_proj = nn.Linear(d_model, d_model, bias=False)
        self.dropout = nn.Dropout(dropout)
        self.rope = RotaryPositionEmbedding(self.d_head, max_seq_len)

    def forward(self, x, causal_mask=True, kv_cache=None, start_pos=0):
        batch, seq_len, _ = x.shape

        qkv = self.qkv_proj(x)
        qkv = qkv.reshape(batch, seq_len, 3, self.n_heads, self.d_head)
        qkv = qkv.permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]

        cos, sin = self.rope(start_pos + seq_len)
        cos = cos[start_pos:start_pos + seq_len]
        sin = sin[start_pos:start_pos + seq_len]
        q, k = apply_rotary_pos_emb(q, k, cos, sin)

        # KV cache for autoregressive generation
        if kv_cache is not None:
            cached_k, cached_v = kv_cache
            k = torch.cat([cached_k, k], dim=2)
            v = torch.cat([cached_v, v], dim=2)
        new_kv_cache = (k, v)

        scale = math.sqrt(self.d_head)
        attn = torch.matmul(q, k.transpose(-2, -1)) / scale

        if causal_mask:
            total_len = k.shape[2]
            mask = torch.triu(torch.ones(seq_len, total_len, device=x.device), diagonal=1 + start_pos).bool()
            attn = attn.masked_fill(mask.unsqueeze(0).unsqueeze(0), float('-inf'))

        attn = F.softmax(attn, dim=-1)
        attn = self.dropout(attn)

        out = torch.matmul(attn, v)
        out = out.transpose(1, 2).reshape(batch, seq_len, self.d_model)
        return self.out_proj(out), new_kv_cache


class SwiGLUFeedForward(nn.Module):
    """SwiGLU feed-forward network: w2(silu(w1(x)) * w3(x))."""

    def __init__(self, d_model, d_ff, dropout=0.1):
        super().__init__()
        self.w1 = nn.Linear(d_model, d_ff, bias=False)  # gate
        self.w3 = nn.Linear(d_model, d_ff, bias=False)  # up
        self.w2 = nn.Linear(d_ff, d_model, bias=False)   # down
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        return self.dropout(self.w2(F.silu(self.w1(x)) * self.w3(x)))


class TransformerBlock(nn.Module):
    def __init__(self, d_model, n_heads, d_ff, dropout=0.1, max_seq_len=2048):
        super().__init__()
        self.norm1 = RMSNorm(d_model)
        self.attn = RoPEMultiHeadAttention(d_model, n_heads, dropout, max_seq_len)
        self.norm2 = RMSNorm(d_model)
        self.ff = SwiGLUFeedForward(d_model, d_ff, dropout)

    def forward(self, x, kv_cache=None, start_pos=0):
        attn_out, new_kv_cache = self.attn(self.norm1(x), kv_cache=kv_cache, start_pos=start_pos)
        x = x + attn_out
        x = x + self.ff(self.norm2(x))
        return x, new_kv_cache


class MusicTransformer(nn.Module):
    """Music Transformer with RoPE, SwiGLU, and RMSNorm (LLaMA-style)."""

    def __init__(self, n_vocab, d_model=256, n_heads=4, n_layers=4, d_ff=1024,
                 max_seq_len=512, dropout=0.1):
        super().__init__()
        self.n_vocab = n_vocab
        self.d_model = d_model
        self.n_heads = n_heads
        self.n_layers = n_layers
        self.d_ff = d_ff
        self.max_seq_len = max_seq_len
        self.dropout_rate = dropout

        self.token_embedding = nn.Embedding(n_vocab, d_model)
        self.embed_dropout = nn.Dropout(dropout)

        self.layers = nn.ModuleList([
            TransformerBlock(d_model, n_heads, d_ff, dropout, max_seq_len)
            for _ in range(n_layers)
        ])

        self.ln_f = RMSNorm(d_model)
        self.output_proj = nn.Linear(d_model, n_vocab, bias=False)
        self.output_proj.weight = self.token_embedding.weight

        self._init_weights()

    def _init_weights(self):
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.normal_(module.weight, mean=0.0, std=0.02)
            elif isinstance(module, nn.Embedding):
                nn.init.normal_(module.weight, mean=0.0, std=0.02)
            elif isinstance(module, RMSNorm):
                nn.init.ones_(module.weight)

    def forward(self, x):
        x = self.token_embedding(x)
        x = self.embed_dropout(x)
        for layer in self.layers:
            x, _ = layer(x)
        x = self.ln_f(x)
        return self.output_proj(x)

    @torch.no_grad()
    def generate_step(self, token, kv_caches=None, start_pos=0):
        """Single autoregressive step with KV cache.

        Args:
            token: (batch, 1) tensor of the latest token.
            kv_caches: list of (k, v) tuples per layer, or None for first step.
            start_pos: position index for RoPE.

        Returns:
            logits: (batch, vocab) logits for next token.
            new_kv_caches: updated KV caches.
        """
        x = self.token_embedding(token)
        new_kv_caches = []
        for i, layer in enumerate(self.layers):
            cache = kv_caches[i] if kv_caches is not None else None
            x, new_cache = layer(x, kv_cache=cache, start_pos=start_pos)
            new_kv_caches.append(new_cache)
        x = self.ln_f(x)
        logits = self.output_proj(x[:, -1, :])
        return logits, new_kv_caches

    def count_parameters(self):
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
