import math
import numpy as np
import pytest
import soundfile as sf
from scripts.audio_qa import analyze, AudioQAReport, write_report

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
    # 90s > 1min 目标 × 1.2 余量 = 72s（brief 原 50s vs 35min 不会超时，已修正）
    make_wav(p, seconds=90.0)
    r = analyze(p, expected_minutes=1.0)
    assert any("时长" in i for i in r.issues)

def test_write_report(tmp_path):
    p = tmp_path / "e.wav"
    make_wav(p, seconds=1.0)
    r = analyze(p)
    out = tmp_path / "audio-qa.json"
    write_report(r, out)
    import json
    assert json.loads(out.read_text(encoding="utf-8"))["duration_s"] == pytest.approx(1.0, abs=0.05)
