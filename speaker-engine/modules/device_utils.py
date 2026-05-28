"""Centralized device / dtype selection for Seed-VC V2 inference."""
import os
import warnings

import torch


def resolve_device() -> torch.device:
    """Select inference device. FORCE_CPU=1 always uses CPU."""
    if os.getenv("FORCE_CPU", "0") == "1":
        return torch.device("cpu")

    if torch.cuda.is_available():
        return torch.device("cuda")

    if torch.backends.mps.is_available():
        return torch.device("mps")

    return torch.device("cpu")


def infer_dtype(device: torch.device) -> torch.dtype:
    """CPU must not use float16; GPU/MPS keep float16 for throughput."""
    if device.type == "cpu":
        return torch.float32
    return torch.float16


# Backward-compatible alias
inference_dtype = infer_dtype


def use_torch_compile_inductor() -> bool:
    """Inductor requires CUDA and must not run when FORCE_CPU is set."""
    if os.getenv("FORCE_CPU", "0") == "1":
        return False
    return torch.cuda.is_available()


def safe_module_to_device(module: torch.nn.Module, device: torch.device) -> torch.nn.Module:
    """Move module to device; fall back to CPU on CUDA / device errors."""
    try:
        return module.to(device)
    except (RuntimeError, AssertionError) as exc:
        if device.type == "cpu":
            raise
        warnings.warn(
            f"Failed to move model to {device} ({exc}); falling back to CPU.",
            RuntimeWarning,
            stacklevel=2,
        )
        return module.to(torch.device("cpu"))
