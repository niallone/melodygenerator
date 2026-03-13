"""Tests for the sampling module."""

import torch


def test_sample_returns_valid_index():
    from app.src.services.sampling import sample_with_top_k_top_p

    logits = torch.randn(100)
    index = sample_with_top_k_top_p(logits, temperature=1.0)
    assert 0 <= index < 100


def test_top_k_limits_candidates():
    from app.src.services.sampling import sample_with_top_k_top_p

    logits = torch.zeros(100)
    logits[42] = 10.0  # Make one token dominant
    index = sample_with_top_k_top_p(logits, temperature=0.1, top_k=1)
    assert index == 42


def test_top_p_nucleus_sampling():
    from app.src.services.sampling import sample_with_top_k_top_p

    logits = torch.full((100,), -10.0)
    logits[0] = 10.0
    logits[1] = 9.0
    # With top_p=0.5 and low temperature, should pick from top tokens
    index = sample_with_top_k_top_p(logits, temperature=0.1, top_p=0.5)
    assert index in (0, 1)


def test_high_temperature_produces_varied_output():
    from app.src.services.sampling import sample_with_top_k_top_p

    logits = torch.zeros(10)
    seen = set()
    for _ in range(200):
        idx = sample_with_top_k_top_p(logits, temperature=2.0)
        seen.add(idx)
    # With uniform logits and high temp, we should see multiple distinct tokens
    assert len(seen) > 1


def test_low_temperature_concentrates():
    from app.src.services.sampling import sample_with_top_k_top_p

    logits = torch.zeros(100)
    logits[7] = 5.0
    results = [sample_with_top_k_top_p(logits, temperature=0.01) for _ in range(50)]
    # With very low temperature, should almost always pick the dominant token
    assert results.count(7) > 40
