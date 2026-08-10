"""试听质检：时长/削波/静音占比/响度/显存。CLI 输出 JSON 报告。"""
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

# 以 `python3 scripts/audio_qa.py ...` 直接运行时 sys.path[0] 是 scripts/，
# 需把仓库根目录加回 path（与 lint_script/lint_voices 同模式）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import soundfile as sf

CLIP_DB = -0.1  # 峰值超过 0dB 视为削波（接近满幅）
SILENCE_THRESHOLD_DB = -45.0
SILENCE_FRAME_MS = 20.0  # 静音判定窗口：按 20ms 帧的 RMS 判，不按单样本幅值
MAX_SILENCE_RUN_S = 3.0  # 最长连续静音段（秒）——超过视为死空气（对话实测最长 0.9s）
MAX_DURATION_TOLERANCE = 1.20
MIN_RMS_DB = -40.0

USAGE = "usage: python3 scripts/audio_qa.py <wav> [out.json] [expected_minutes]"


@dataclass
class AudioQAReport:
    duration_s: float = 0.0
    peak_db: float = -float("inf")
    clipping: bool = False
    silence_ratio: float = 0.0
    max_silence_run_s: float = 0.0
    rms_db: float = -float("inf")
    issues: list[str] = None
    vram_gb: float = 0.0

    def __post_init__(self):
        if self.issues is None:
            self.issues = []


def _db(x: float) -> float:
    return 20.0 * np.log10(max(x, 1e-10))


def _silence_ratio(x: np.ndarray, sr: int) -> tuple[float, float]:
    """按 20ms 帧 RMS 判定静音（低于 -45dB 的帧视为静音帧），返回 (静音帧占比, 最长连续静音段秒数)。

    样本级口径（|x|<阈值 的样本占比）会把 -45dB 以下的帧内
    "大部分样本略低于阈值"也计为静音，导致响度正常的口播被误报高静音。
    """
    frame = int(sr * SILENCE_FRAME_MS / 1000)
    if frame < 1:
        frame = 1
    n_frames = len(x) // frame
    if n_frames < 1:
        allsil = float(np.all(np.abs(x) < 10 ** (SILENCE_THRESHOLD_DB / 20)))
        return allsil, (len(x) / sr if allsil else 0.0)
    frames = x[: n_frames * frame].reshape(n_frames, frame)
    rms = np.sqrt(np.mean(frames ** 2, axis=1) + 1e-12)
    is_sil = rms < 10 ** (SILENCE_THRESHOLD_DB / 20)
    # 最长连续静音段（帧级）
    max_run = 0
    cur = 0
    for s in is_sil:
        cur = cur + 1 if s else 0
        max_run = max(max_run, cur)
    return float(np.mean(is_sil)), max_run * SILENCE_FRAME_MS / 1000.0


def analyze(path: Path, expected_minutes: float = 35.0) -> AudioQAReport:
    path = Path(path)
    x, sr = sf.read(str(path), dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)
    r = AudioQAReport()
    r.duration_s = len(x) / sr
    r.peak_db = _db(float(np.abs(x).max()))
    r.clipping = bool(r.peak_db > CLIP_DB)  # bool()：np.bool_ 不可 JSON 序列化
    rms = float(np.sqrt(np.mean(x ** 2)))
    r.rms_db = _db(rms)
    r.silence_ratio, r.max_silence_run_s = _silence_ratio(x, sr)

    target_s = expected_minutes * 60
    if r.duration_s > target_s * MAX_DURATION_TOLERANCE:
        r.issues.append(f"BLOCKING: 时长 {r.duration_s:.0f}s 超目标 {target_s:.0f}s 的 20% 余量")
    if r.clipping:
        r.issues.append(f"BLOCKING: 峰值 {r.peak_db:.1f}dB 削波")
    # 静音占比：对话节目有自然轮次间隙（~30%），参考值 35%
    # （连续口播 2-9%；对话实测 30%，分解为 10% 咬字间隙 + 8% 词间 + 12% 句间）
    if r.silence_ratio > 0.35:
        r.issues.append(f"WARN: 静音占比 {r.silence_ratio:.0%} > 35%")
    if r.max_silence_run_s > MAX_SILENCE_RUN_S:
        r.issues.append(f"BLOCKING: 最长静音段 {r.max_silence_run_s:.1f}s > {MAX_SILENCE_RUN_S:.0f}s（疑似死空气）")
    if r.rms_db < MIN_RMS_DB:
        r.issues.append(f"WARN: 响度 {r.rms_db:.1f}dB 偏低（< {MIN_RMS_DB}dB）")
    return r


def write_report(report: AudioQAReport, path: Path) -> None:
    path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(USAGE, file=sys.stderr)
        return 2
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
