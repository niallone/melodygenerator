from shared.models import MelodyLSTM


class ModelBuilder:
    """
    A class for building the neural network model.
    """

    def create_model(self, network_input, n_vocab, embedding_dim=128,
                     use_attention=False, num_attention_heads=4, model_version=None):
        print(f"Creating model with input shape {network_input.shape} and {n_vocab} vocabulary size...")
        model = MelodyLSTM(
            n_vocab, embedding_dim=embedding_dim,
            use_attention=use_attention, num_attention_heads=num_attention_heads,
            model_version=model_version,
        )
        print(f"Model created successfully (version={model.model_version}, embedding_dim={embedding_dim}, attention={use_attention})")
        return model
