### Task 5: tts.py — TTS 抽象 + 本地 provider 骨架

**Files:**
- Create: `scripts/tts.py`
- Test: `tests/test_tts_abstraction.py`

**Interfaces:**
- Produces:
  - `@dataclass TTSOpts`: `sample_rate=24000`、`max_new_tokens: int | None`、`temperature=0.6`、`top_k=50`、`top_p=0.9`
  - `@dataclass VoiceSpec`: `name`、`ref_audio: Path | None`
  - `@dataclass AudioBundle`: `wav_path: Path`、`segments: list[Path]`、`duration_s: float`、`vram_gb: float`
  - `class TTSProvider(Protocol)`: `synthesize(script: Script, voice_map: dict[str, VoiceSpec], opts: TTSOpts) -> AudioBundle`、`list_voices() -> list[VoiceSpec]`、`native_dialogue -> bool`
  - `class LocalTTSProvider`: `__init__(model_dir, device="cuda:0", dtype="bfloat16")`、`warmup()`、`vram_report() -> dict`
  - `class DialogueTTSProvider(LocalTTSProvider)`: `native_dialogue = True`（MOSS-TTSD 挂接点；synthesize 先抛 NotImplementedError，Task 17 装真模型后实现）
  - `class SegmentedTTSProvider(LocalTTSProvider)`: `native_dialogue = False`，类常量 `PAUSE_SPEAKER_SWITCH_MS=(350,500)`、`PAUSE_SAME_SPEAKER_MS=(150,250)`（CosyVoice3 fallback 挂接点）
  - `load_provider(config: dict) -> TTSProvider`（按 devpodcast.json `tts.provider` 键分派；未知键抛 ValueError）

- [ ] **Step 1: 写失败测试**

```python
# tests/test_tts_abstraction.py
import pytest
from scripts.tts import (DialogueTTSProvider, SegmentedTTSProvider, load_provider,
                         TTSProvider, TTSOpts)

def test_dialogue_provider_native_flag():
    p = DialogueTTSProvider(model_dir="/tmp/nonexistent")
    assert p.native_dialogue is True

def test_segmented_provider_pause_constants():
    p = SegmentedTTSProvider(model_dir="/tmp/nonexistent")
    assert p.PAUSE_SPEAKER_SWITCH_MS == (350, 500)
    assert p.PAUSE_SAME_SPEAKER_MS == (150, 250)

def test_load_provider_dispatch():
    p = load_provider({"provider": "moss-ttsd"})
    assert isinstance(p, DialogueTTSProvider)
    p2 = load_provider({"provider": "cosyvoice3"})
    assert isinstance(p2, SegmentedTTSProvider)

def test_load_provider_unknown_raises():
    with pytest.raises(ValueError):
        load_provider({"provider": "nope"})

def test_synthesize_not_implemented_yet():
    p = DialogueTTSProvider(model_dir="/tmp/nonexistent")
    with pytest.raises(NotImplementedError):
        p.synthesize(script=None, voice_map={}, opts=TTSOpts())

def test_implements_protocol():
    assert isinstance(DialogueTTSProvider(model_dir="/tmp/nonexistent"), TTSProvider)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_tts_abstraction.py -v`
Expected: FAIL

- [ ] **Step 3: 写实现**

```python
# scripts/tts.py
"""TTS 抽象层：DialogueTTSProvider（MOSS-TTSD，原生对话）与 SegmentedTTSProvider
（CosyVoice3，逐句+拼接）两类，统一 Protocol。本地基类管理 GPU/batch/预热/显存。"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

# 需在 M0 环境任务（Task 17）安装 torch；本文件顶层不 import torch，避免无 GPU 环境崩溃。


@dataclass
class TTSOpts:
    sample_rate: int = 24000
    max_new_tokens: int | None = None
    temperature: float = 0.6
    top_k: int = 50
    top_p: float = 0.9


@dataclass
class VoiceSpec:
    name: str
    ref_audio: Path | None = None


@dataclass
class AudioBundle:
    wav_path: Path
    segments: list[Path] = field(default_factory=list)
    duration_s: float = 0.0
    vram_gb: float = 0.0


class TTSProvider(Protocol):
    native_dialogue: bool

    def synthesize(self, script, voice_map: dict, opts: TTSOpts) -> AudioBundle: ...
    def list_voices(self) -> list[VoiceSpec]: ...


class LocalTTSProvider:
    """本地基类：GPU 设备管理、模型预热、显存报告。子类实现 synthesize。"""

    def __init__(self, model_dir: str | Path, device: str = "cuda:0", dtype: str = "bfloat16"):
        self.model_dir = Path(model_dir)
        self.device = device
        self.dtype = dtype

    def warmup(self) -> None:
        """预热到稳态：子类实现（Task 17 真装模型后）。"""
        raise NotImplementedError

    def vram_report(self) -> dict:
        try:
            import torch
        except ImportError:
            return {"error": "torch not installed"}
        if not torch.cuda.is_available():
            return {"error": "cuda not available"}
        props = torch.cuda.get_device_properties(0)
        return {"device": torch.cuda.get_device_name(0),
                "total_gb": round(props.total_memory / 1024 ** 3, 1),
                "used_gb": round((props.total_memory - torch.cuda.mem_get_info(0)[0]) / 1024 ** 3, 1)}


class DialogueTTSProvider(LocalTTSProvider):
    """MOSS-TTSD：整段对话一次合成。Script → [S1]/[S2] 标签串 → 单次生成。"""
    native_dialogue = True

    def synthesize(self, script, voice_map: dict, opts: TTSOpts) -> AudioBundle:
        raise NotImplementedError("MOSS-TTSD 模型接入在 Task 17（M0 环境）")


class SegmentedTTSProvider(LocalTTSProvider):
    """CosyVoice3：逐句合成 + 规则插静音拼接。"""
    native_dialogue = False
    PAUSE_SPEAKER_SWITCH_MS = (350, 500)
    PAUSE_SAME_SPEAKER_MS = (150, 250)

    def synthesize(self, script, voice_map: dict, opts: TTSOpts) -> AudioBundle:
        raise NotImplementedError("CosyVoice3 模型接入在 fallback 任务")


def load_provider(config: dict) -> TTSProvider:
    kind = config.get("provider", "")
    if kind == "moss-ttsd":
        return DialogueTTSProvider(model_dir=config.get("model_dir", "models/moss-ttsd"))
    if kind == "cosyvoice3":
        return SegmentedTTSProvider(model_dir=config.get("model_dir", "models/cosyvoice3"))
    raise ValueError(f"未知 TTS provider: {kind!r}")
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_tts_abstraction.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/tts.py tests/test_tts_abstraction.py
git commit -m "feat: TTS 抽象层（对话/分段两类 provider + 本地基类）"
```

---

### Task 6: voice_budget.py — 时长/节奏预算
