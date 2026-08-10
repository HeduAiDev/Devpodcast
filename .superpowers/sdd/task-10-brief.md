### Task 10: audio_qa.py — 试听质检

**Files:**
- Create: `scripts/audio_qa.py`
- Test: `tests/test_audio_qa.py`

**Interfaces:**
- Produces:
  - `@dataclass AudioQAReport`: `duration_s / peak_db / clipping: bool / silence_ratio: float / rms_db: float / issues: list[str] / vram_gb: float`
  - `analyze(path: Path, expected_minutes: float = 35.0) -> AudioQAReport`
  - `write_report(report, path)`（audio-qa.json）
  - 检查：时长超目标 20% → BLOCKING；clipping → BLOCKING；静音占比 > 25% → WARN；RMS < -40dB → WARN（太轻）

**依赖：`soundfile`（numpy 已随 torch 装）。** 测试用合成正弦波。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_audio_qa.py
import math
import numpy as np
import pytest
import soundfile as sf
from scripts.audio_qa import analyze, AudioQAReport

def make_wav(path, seconds=2.0, sr=24000, freq=440.0, amp=0.5, silence_frac=0.1):
    n = int(seconds * sr)
    t = np.arange(n) / sr
    x = amp * np.sin(2 * math.pi * freq * t).astype(np.float32)
    sil = int(n * silence_frac)
    x[:sil] = 0.0
    sf.write(str(path), x, sr)

def test_basic_duration(tmp_path):
    p = tmp_path / "a.wav"
    make_wav(p, seconds=2.0)
    r = analyze(p, expected_minutes=35.0)
    assert r.duration_s == pytest.approx(2.0, abs=0.05)
    assert not r.clipping
    assert r.peak_db < 0.0

def test_clipping_detected(tmp_path):
    p = tmp_path / "b.wav"
    make_wav(p, seconds=1.0, amp=2.0)  # 削波
    r = analyze(p)
    assert r.clipping

def test_silence_ratio(tmp_path):
    p = tmp_path / "c.wav"
    make_wav(p, seconds=4.0, silence_frac=0.5)
    r = analyze(p)
    assert r.silence_ratio > 0.4

def test_over_duration_blocking(tmp_path):
    p = tmp_path / "d.wav"
    make_wav(p, seconds=50.0)  # 目标 35min 的 20% 余量外
    r = analyze(p, expected_minutes=35.0)
    assert any("时长" in i for i in r.issues)

def test_write_report(tmp_path):
    p = tmp_path / "e.wav"
    make_wav(p, seconds=1.0)
    r = analyze(p)
    out = tmp_path / "audio-qa.json"
    write_report(r, out)
    import json
    assert json.loads(out.read_text(encoding="utf-8"))["duration_s"] == pytest.approx(1.0, abs=0.05)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest tests/test_audio_qa.py -v`
Expected: FAIL（audio_qa 未定义）

- [ ] **Step 3: 写实现**

```python
# scripts/audio_qa.py
"""试听质检：时长/削波/静音占比/响度/显存。CLI 输出 JSON 报告。"""
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import soundfile as sf

CLIP_DB = -0.1  # 峰值超过 0dB 视为削波（接近满幅）
SILENCE_THRESHOLD_DB = -45.0
MAX_DURATION_TOLERANCE = 1.20
MIN_RMS_DB = -40.0


@dataclass
class AudioQAReport:
    duration_s: float = 0.0
    peak_db: float = -float("inf")
    clipping: bool = False
    silence_ratio: float = 0.0
    rms_db: float = -float("inf")
    issues: list[str] = None
    vram_gb: float = 0.0

    def __post_init__(self):
        if self.issues is None:
            self.issues = []


def _db(x: float) -> float:
    return 20.0 * np.log10(max(x, 1e-10))


def analyze(path: Path, expected_minutes: float = 35.0) -> AudioQAReport:
    path = Path(path)
    x, sr = sf.read(str(path), dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)
    r = AudioQAReport()
    r.duration_s = len(x) / sr
    r.peak_db = _db(float(np.abs(x).max()))
    r.clipping = r.peak_db > CLIP_DB
    rms = float(np.sqrt(np.mean(x ** 2)))
    r.rms_db = _db(rms)
    sil = x[np.abs(x) < 10 ** (SILENCE_THRESHOLD_DB / 20)]
    r.silence_ratio = len(sil) / len(x)

    target_s = expected_minutes * 60
    if r.duration_s > target_s * MAX_DURATION_TOLERANCE:
        r.issues.append(f"BLOCKING: 时长 {r.duration_s:.0f}s 超目标 {target_s:.0f}s 的 20% 余量")
    if r.clipping:
        r.issues.append(f"BLOCKING: 峰值 {r.peak_db:.1f}dB 削波")
    if r.silence_ratio > 0.25:
        r.issues.append(f"WARN: 静音占比 {r.silence_ratio:.0%} > 25%")
    if r.rms_db < MIN_RMS_DB:
        r.issues.append(f"WARN: 响度 {r.rms_db:.1f}dB 偏低（< {MIN_RMS_DB}dB）")
    return r


def write_report(report: AudioQAReport, path: Path) -> None:
    path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    wav = Path(argv[0])
    out = Path(argv[1]) if len(argv) > 1 else wav.with_suffix(".audio-qa.json")
    expected = float(argv[2]) if len(argv) > 2 else 35.0
    r = analyze(wav, expected)
    write_report(r, out)
    for i in r.issues:
        print(f"[{'BLOCKING' if i.startswith('BLOCKING') else 'WARN'}] {i}")
    return 1 if any(i.startswith("BLOCKING") for i in r.issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest tests/test_audio_qa.py -v`
Expected: PASS

（若无 soundfile：`pip install soundfile`，或先用 `wave` 模块实现读取。**优先 soundfile，需保证测试环境装好再开工**。）

- [ ] **Step 5: 提交**

```bash
git add scripts/audio_qa.py tests/test_audio_qa.py
git commit -m "feat: audio_qa 试听质检（时长/削波/静音/响度）"
```

---

### Task 11: season_bible.py + archivist.py
