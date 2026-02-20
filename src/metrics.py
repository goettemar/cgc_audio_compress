"""Audio quality metrics — SNR and Spectral Convergence."""

from __future__ import annotations

import torch
import numpy as np


def snr_db(original: torch.Tensor, reconstructed: torch.Tensor) -> float:
    """Signal-to-Noise Ratio in dB.

    Both tensors should have shape (channels, samples).
    """
    # Align lengths
    min_len = min(original.shape[-1], reconstructed.shape[-1])
    orig = original[..., :min_len].float()
    recon = reconstructed[..., :min_len].float()

    noise = orig - recon
    signal_power = (orig ** 2).mean()
    noise_power = (noise ** 2).mean()

    if noise_power < 1e-10:
        return float("inf")

    return 10.0 * torch.log10(signal_power / noise_power).item()


def spectral_convergence(original: torch.Tensor, reconstructed: torch.Tensor) -> float:
    """Spectral Convergence (lower is better, 0 = perfect).

    Computed as ||STFT(orig) - STFT(recon)|| / ||STFT(orig)||.
    Both tensors should have shape (channels, samples).
    """
    min_len = min(original.shape[-1], reconstructed.shape[-1])
    orig = original[..., :min_len].float()
    recon = reconstructed[..., :min_len].float()

    # Mix to mono for spectral comparison
    if orig.dim() > 1 and orig.shape[0] > 1:
        orig = orig.mean(dim=0)
        recon = recon.mean(dim=0)
    else:
        orig = orig.squeeze(0)
        recon = recon.squeeze(0)

    # Compute STFT magnitudes
    n_fft = 2048
    hop_length = 512
    window = torch.hann_window(n_fft, device=orig.device)

    spec_orig = torch.stft(orig, n_fft, hop_length, window=window, return_complex=True).abs()
    spec_recon = torch.stft(recon, n_fft, hop_length, window=window, return_complex=True).abs()

    norm_diff = torch.norm(spec_orig - spec_recon)
    norm_orig = torch.norm(spec_orig)

    if norm_orig < 1e-10:
        return 0.0

    return (norm_diff / norm_orig).item()
