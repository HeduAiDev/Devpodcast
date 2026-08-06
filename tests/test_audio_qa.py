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


def test_silence_ratio_frame_level_not_sample_level(tmp_path):
    """低幅但可听的正弦（RMS -30dB）不该被判成静音。

    样本级口径（|x| < -45dB 的样本占比）会把这段算成 ~30% 静音——正弦
    过零附近的样本天然低于阈值。帧级 RMS 口径下应接近 0%。
    """
    p = tmp_path / "quiet.wav"
    make_wav(p, seconds=4.0, amp=0.0447, silence_frac=0.0)  # RMS ≈ -30dB
    r = analyze(p)
    assert r.rms_db == pytest.approx(-30.0, abs=1.5)
    assert r.silence_ratio < 0.05


def test_silence_ratio_counts_true_silence_frames(tmp_path):
    """真静音（整段置 0）必须照常计入，帧级口径不能漏报。"""
    p = tmp_path / "half.wav"
    make_wav(p, seconds=4.0, silence_frac=0.25)
    r = analyze(p)
    assert r.silence_ratio == pytest.approx(0.25, abs=0.03)


def test_dead_air_blocking(tmp_path):
    """连续 4s 死空气 → BLOCKING（占比口径漏不掉的才是真问题）。"""
    p = tmp_path / "dead.wav"
    make_wav(p, seconds=20.0, silence_frac=0.2)  # 前 4s 全 0
    r = analyze(p, expected_minutes=35.0)
    assert r.max_silence_run_s == pytest.approx(4.0, abs=0.1)
    assert any(i.startswith("BLOCKING") and "死空气" in i for i in r.issues)


def test_dialogue_pacing_not_flagged(tmp_path):
    """对话式停顿（多个 0.5s 间隙，总占比 ~30%）不该报 WARN——阈值 35%。"""
    sr = 24000
    seg = []
    for _ in range(12):
        t = np.arange(int(1.2 * sr)) / sr
        seg.append((0.5 * np.sin(2 * math.pi * 440 * t)).astype(np.float32))
        seg.append(np.zeros(int(0.5 * sr), dtype=np.float32))
    p = tmp_path / "dialogue.wav"
    sf.write(str(p), np.concatenate(seg), sr)
    r = analyze(p, expected_minutes=35.0)
    assert 0.25 < r.silence_ratio < 0.35
    assert r.issues == []

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
