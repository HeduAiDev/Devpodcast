"""torchaudio 兼容层：Windows 无 FFmpeg DLL 时退回 soundfile。

torchaudio 2.11+ 默认使用 torchcodec 解码器（依赖 FFmpeg 共享库）。若系统无
FFmpeg 会抛 RuntimeError。本模块 monkey-patch torchaudio.load() 到 soundfile，
在导入时自动生效。

Usage:
    import scripts.ta_compat  # 在 import torchaudio 之前
    import torchaudio          # 此后 torchaudio.load() 走 soundfile
"""

import soundfile as sf
import torch

_ORIG_LOAD = None
_PATCHED = False


def _sf_load(uri: str, *args, **kwargs):
    """soundfile-backed replacement for torchaudio.load()."""
    data, sample_rate = sf.read(str(uri), dtype="float32")
    if data.ndim == 1:
        data = data[:, None]  # (samples,) → (samples, 1)
    # torchaudio convention: (channels, samples)
    return torch.from_numpy(data).T.contiguous(), sample_rate


def _patch():
    global _PATCHED, _ORIG_LOAD
    if _PATCHED:
        return
    try:
        import torchaudio
        _ORIG_LOAD = torchaudio.load
        torchaudio.load = _sf_load
        _PATCHED = True
    except ImportError:
        pass


def _unpatch():
    global _PATCHED
    if not _PATCHED:
        return
    try:
        import torchaudio
        torchaudio.load = _ORIG_LOAD
        _PATCHED = False
    except ImportError:
        pass


def is_patched() -> bool:
    return _PATCHED


# Auto-patch on import
_patch()
