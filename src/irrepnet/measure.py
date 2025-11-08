
from __future__ import annotations

import math
from typing import Iterable, List, Optional, Sequence

import torch


def _real_dtype_for_device(device: torch.device) -> torch.dtype:
    """Return an MPS-safe floating dtype (defaults to float64 otherwise)."""
    if device.type == "mps":
        return torch.float32
    return torch.float64


def roots_of_unity(k: int, *, device: torch.device, real_dtype: torch.dtype) -> torch.Tensor:
    g = torch.arange(k, device=device, dtype=real_dtype)
    theta = (2.0 * math.pi * g) / float(k)
    ones = torch.ones(k, device=device, dtype=real_dtype)
    return torch.polar(ones, theta)


def measure_counts(
    counts: torch.Tensor,
    readout_edges: Sequence[int],
    k: int,
    channels: Optional[Sequence[int]] = None,
) -> float:
    if not readout_edges:
        return 0.0

    device = counts.device
    real_dtype = _real_dtype_for_device(device)
    complex_dtype = torch.complex64 if real_dtype == torch.float32 else torch.complex128

    edge_idx = torch.tensor(readout_edges, dtype=torch.long, device=device)
    selected = counts.index_select(0, edge_idx)  # [E_sel, C, k]

    if channels is not None:
        if not isinstance(channels, Iterable):
            raise ValueError("E_MEASURE_CHANNELS_EXPECTED_ITERABLE")
        channel_idx = torch.tensor(list(channels), dtype=torch.long, device=device)
        selected = selected.index_select(1, channel_idx)

    n_g = selected.sum(dim=(0, 1)).to(real_dtype)  # [k]
    chi = roots_of_unity(k, device=device, real_dtype=real_dtype).to(complex_dtype)  # [k]
    amplitude = (n_g.to(complex_dtype) * chi).sum()
    return float(amplitude.abs().pow(2).item())
