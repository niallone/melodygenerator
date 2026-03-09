import torch.nn as nn


class MelodyLSTM(nn.Module):
    """
    PyTorch LSTM model for music generation.

    Supports variable hidden sizes per layer to handle different model versions.
    Uses separate LSTM layers rather than a single stacked one.
    Output is raw logits (use CrossEntropyLoss).

    Model versions:
      v1 (legacy): input_size=1, float input / n_vocab (embedding_dim=0)
      v2+: nn.Embedding, int64 input (embedding_dim>0)
      v4+: + MultiheadAttention after LSTM stack
    """

    def __init__(self, n_vocab, lstm_units=None, dense_units=256, dropout=0.3,
                 embedding_dim=0, use_attention=False, num_attention_heads=4,
                 model_version=None):
        super().__init__()
        if lstm_units is None:
            lstm_units = [512, 512, 512]

        self.n_vocab = n_vocab
        self.lstm_units = lstm_units
        self.dense_units = dense_units
        self.num_layers = len(lstm_units)
        self.embedding_dim = embedding_dim
        self.use_attention = use_attention
        self.num_attention_heads = num_attention_heads

        # Use explicit version if provided, otherwise infer
        if model_version is not None:
            self.model_version = model_version
        elif use_attention:
            self.model_version = 4
        elif embedding_dim > 0:
            self.model_version = 2
        else:
            self.model_version = 1

        # Embedding layer (v2+)
        if embedding_dim > 0:
            self.embedding = nn.Embedding(n_vocab, embedding_dim)
            first_input_size = embedding_dim
        else:
            self.embedding = None
            first_input_size = 1

        # LSTM layers
        self.lstm_layers = nn.ModuleList()
        self.dropout_layers = nn.ModuleList()
        for i, units in enumerate(lstm_units):
            input_size = first_input_size if i == 0 else lstm_units[i - 1]
            self.lstm_layers.append(nn.LSTM(
                input_size=input_size,
                hidden_size=units,
                batch_first=True,
            ))
            self.dropout_layers.append(nn.Dropout(dropout))

        # Attention layer (v4+)
        if use_attention:
            self.attention = nn.MultiheadAttention(
                embed_dim=lstm_units[-1], num_heads=num_attention_heads, batch_first=True
            )
            self.attention_norm = nn.LayerNorm(lstm_units[-1])

        self.fc1 = nn.Linear(lstm_units[-1], dense_units)
        self.fc_dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(dense_units, n_vocab)

    def forward(self, x):
        if self.embedding is not None:
            out = self.embedding(x)
        else:
            out = x

        for i, (lstm, dropout) in enumerate(zip(self.lstm_layers, self.dropout_layers)):
            out, _ = lstm(out)
            if i < self.num_layers - 1:
                out = dropout(out)

        if self.use_attention:
            residual = out
            attn_out, _ = self.attention(out, out, out)
            out = self.attention_norm(residual + attn_out)

        last_output = out[:, -1, :]
        out = self.fc1(last_output)
        out = self.fc_dropout(out)
        out = self.fc2(out)
        return out
