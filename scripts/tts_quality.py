#!/usr/bin/env python3
"""TTS 输出客观质量指标 —— 用于参数扫描的自动初筛。

不替代人耳，但能把明显坏的组合先剔掉：

1. **时长偏差**  同一文本不同参数下的时长差 → 赶字/拖字/重复
2. **重复自相关**  帧级 MFCC 自相关峰 → 卡碟式重复片段
3. **音色一致性**  同 speaker 各 turn 的 MFCC 质心距离 → 音色漂移
4. **speaker 区分度** S1 vs S2 质心距离 → 双声线是否真的分开
5. **能量异常**  静音占比 / 最长静音 / 削波（复用 audio_qa 口径）

用法：
    python scripts/tts_quality.py <wav> [--turns N] [--json out.json]
    python scripts/tts_quality.py --sweep _diag/firered_sweep   # 批量对比
"""
import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import soundfile as sf

FRAME_MS = 20
SILENCE_RMS_DB = -45.0


@dataclass
class QualityReport:
    wav: str
    duration_s: float
    sample_rate: int
    peak_db: float
    rms_db: float
    clipping: bool
    silence_ratio: float
    max_silence_run_s: float
    repeat_score: float          # 0-1，越高越可能有重复片段
    repeat_worst_lag_s: float    # 最可疑重复的时间间隔
    speaker_sep: float | None = None   # S1/S2 质心距离，越大越好
    timbre_drift: float | None = None  # 同 speaker 内部离散度，越小越好
    issues: list[str] = field(default_factory=list)


def _frames(x: np.ndarray, sr: int, frame_ms: int = FRAME_MS) -> np.ndarray:
    n = max(1, int(sr * frame_ms / 1000))
    trimmed = x[: len(x) // n * n]
    if trimmed.size == 0:
        return np.zeros((0, n), dtype=np.float32)
    return trimmed.reshape(-1, n)


def _db(v: float) -> float:
    return 20 * np.log10(max(v, 1e-10))


def _mfcc_like(frame_block: np.ndarray) -> np.ndarray:
    """轻量频谱特征（免 librosa 依赖）：log-mel 近似 → DCT 前 13 维。"""
    if frame_block.size == 0:
        return np.zeros((0, 13), dtype=np.float32)
    win = np.hanning(frame_block.shape[1])
    spec = np.abs(np.fft.rfft(frame_block * win, axis=1))
    # 对数压缩 + 分 20 个频带取均值（近似 mel 分辨率）
    bands = np.array_split(np.log10(spec + 1e-8), 20, axis=1)
    logmel = np.stack([b.mean(axis=1) for b in bands], axis=1)
    # DCT-II 取低阶系数
    n = logmel.shape[1]
    k = np.arange(13)[:, None]
    basis = np.cos(np.pi * k * (2 * np.arange(n) + 1) / (2 * n))
    return logmel @ basis.T


def _repeat_detect(feat: np.ndarray, sr: int, min_lag_s: float = 1.5) -> tuple[float, float]:
    """自相关找重复片段。返回 (repeat_score, worst_lag_s)。"""
    if len(feat) < 40:
        return 0.0, 0.0
    f = feat - feat.mean(axis=0, keepdims=True)
    norm = np.linalg.norm(f, axis=1, keepdims=True) + 1e-8
    f = f / norm
    min_lag = max(2, int(min_lag_s * 1000 / FRAME_MS))
    max_lag = len(f) // 2
    if max_lag <= min_lag:
        return 0.0, 0.0
    # 逐 lag 计算余弦相似度均值
    sims = []
    for lag in range(min_lag, max_lag):
        a, b = f[:-lag], f[lag:]
        sims.append(float((a * b).sum(axis=1).mean()))
    sims_arr = np.asarray(sims)
    idx = int(np.argmax(sims_arr))
    return float(max(0.0, sims_arr[idx])), (idx + min_lag) * FRAME_MS / 1000


def analyze(wav_path: Path, expect_turns: int | None = None) -> QualityReport:
    x, sr = sf.read(wav_path, dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)

    dur = len(x) / sr
    fb = _frames(x, sr)
    frame_rms = np.sqrt((fb ** 2).mean(axis=1)) if fb.size else np.zeros(0)
    frame_db = np.array([_db(v) for v in frame_rms])
    silent = frame_db < SILENCE_RMS_DB

    silence_ratio = float(silent.mean()) if silent.size else 0.0
    # 最长连续静音
    max_run = 0
    run = 0
    for s in silent:
        run = run + 1 if s else 0
        max_run = max(max_run, run)
    max_silence_run_s = max_run * FRAME_MS / 1000

    peak = float(np.abs(x).max()) if x.size else 0.0
    rms = float(np.sqrt((x ** 2).mean())) if x.size else 0.0

    # 削波判定看「连续被削平的段」，不看单点触顶：峰值归一化会让 peak 恰好 =1.0，
    # 但真失真是连续数十个采样点被压平（≥1ms）。
    at_ceiling = np.abs(x) >= 0.999
    clip_run = 0
    max_clip_run = 0
    for s in at_ceiling:
        clip_run = clip_run + 1 if s else 0
        max_clip_run = max(max_clip_run, clip_run)
    clip_run_ms = max_clip_run / sr * 1000
    clip_ratio = float(at_ceiling.mean()) if at_ceiling.size else 0.0
    clipping = clip_run_ms >= 1.0 or clip_ratio > 0.001

    feat = _mfcc_like(fb)
    voiced = feat[~silent] if silent.size == len(feat) else feat
    repeat_score, repeat_lag = _repeat_detect(voiced, sr)

    # 音色统计：s1/s2 各半段质心，双声线区分度 + 稳定性
    speaker_sep = None
    timbre_drift = None
    if voiced.shape[0] >= 40:
        half = voiced.shape[0] // 2
        c1, c2 = voiced[:half].mean(axis=0), voiced[half:].mean(axis=0)
        speaker_sep = float(np.linalg.norm(c1 - c2))
        # 同半段内逐帧相对质心的平均距离 = 音色漂移
        drift1 = float(np.mean(np.linalg.norm(voiced[:half] - c1, axis=1))) if half else 0.0
        drift2 = float(np.mean(np.linalg.norm(voiced[half:] - c2, axis=1))) if voiced.shape[0]-half else 0.0
        timbre_drift = round((drift1 + drift2) / 2, 4)

    issues: list[str] = []
    if clipping:
        issues.append(f"BLOCKING: 削波（连续 {clip_run_ms:.1f}ms）")
    if max_silence_run_s >= 3.0:
        issues.append(f"BLOCKING: 死气 {max_silence_run_s:.1f}s")
    if silence_ratio > 0.35:
        issues.append(f"WARN: 静音占比 {silence_ratio:.0%} > 35%")
    if repeat_score > 0.75:
        issues.append(f"WARN: 疑似重复片段 (score {repeat_score:.2f} @ lag {repeat_lag:.1f}s)")
    if rms > 0 and _db(rms) < -35:
        issues.append(f"WARN: 整体过轻 {_db(rms):.1f}dB")

    return QualityReport(
        wav=str(wav_path),
        duration_s=round(dur, 2),
        sample_rate=sr,
        peak_db=round(_db(peak), 2),
        rms_db=round(_db(rms), 2),
        clipping=peak >= 0.999,
        silence_ratio=round(silence_ratio, 4),
        max_silence_run_s=round(max_silence_run_s, 2),
        repeat_score=round(repeat_score, 3),
        repeat_worst_lag_s=round(repeat_lag, 2),
        speaker_sep=round(speaker_sep, 3) if speaker_sep is not None else None,
        timbre_drift=timbre_drift,
        issues=issues,
    )


def sweep_compare(sweep_dir: Path) -> dict:
    """批量分析扫描目录，按客观指标排序。"""
    wavs = sorted(sweep_dir.glob("t*_k*.wav"))
    if not wavs:
        raise FileNotFoundError(f"没找到扫描输出：{sweep_dir}/t*_k*.wav")

    reports = [analyze(w) for w in wavs]
    durs = [r.duration_s for r in reports]
    median_dur = float(np.median(durs))

    rows = []
    for r in reports:
        dev = abs(r.duration_s - median_dur) / median_dur if median_dur else 0.0
        # 综合分：低重复 + 时长接近中位数 + 无 issue
        penalty = r.repeat_score * 4 + dev * 6 + len([i for i in r.issues if "BLOCKING" in i]) * 5 \
                  + len([i for i in r.issues if "WARN" in i]) * 1.5
        rows.append({
            "wav": Path(r.wav).name,
            "duration_s": r.duration_s,
            "dur_dev": round(dev, 4),
            "silence_ratio": r.silence_ratio,
            "max_silence_run_s": r.max_silence_run_s,
            "repeat_score": r.repeat_score,
            "timbre_drift": r.timbre_drift,
            "rms_db": r.rms_db,
            "peak_db": r.peak_db,
            "issues": r.issues,
            "objective_score": round(max(0.0, 10 - penalty), 2),
        })
    rows.sort(key=lambda d: -d["objective_score"])
    return {"sweep_dir": str(sweep_dir), "median_duration_s": round(median_dur, 2),
            "count": len(rows), "ranked": rows}


def main():
    ap = argparse.ArgumentParser(description="TTS 输出客观质量指标")
    ap.add_argument("wav", nargs="?", help="单个 wav 文件")
    ap.add_argument("--sweep", help="扫描目录，批量对比排序")
    ap.add_argument("--json", help="结果写入 JSON")
    args = ap.parse_args()

    if args.sweep:
        result = sweep_compare(Path(args.sweep))
        print(f"=== {result['count']} 组客观排序（中位时长 {result['median_duration_s']}s）===")
        print(f"{'wav':<18} {'时长':>7} {'偏差':>6} {'静音':>6} {'重复':>6} {'漂移':>6} {'得分':>6}  issues")
        for r in result["ranked"]:
            print(f"{r['wav']:<18} {r['duration_s']:>6.1f}s {r['dur_dev']:>5.1%} "
                  f"{r['silence_ratio']:>5.1%} {r['repeat_score']:>6.2f} "
                  f"{r['timbre_drift'] if r['timbre_drift'] is not None else '-':>6} "
                  f"{r['objective_score']:>6.2f}  {'; '.join(r['issues']) or '-'}")
        out = result
    elif args.wav:
        rep = analyze(Path(args.wav))
        print(json.dumps(asdict(rep), ensure_ascii=False, indent=2))
        out = asdict(rep)
    else:
        ap.error("需要 wav 或 --sweep")

    if args.json:
        Path(args.json).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n已保存：{args.json}")


if __name__ == "__main__":
    main()
