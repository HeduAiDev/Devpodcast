#!/usr/bin/env python3
"""IndexTTS-2 单句合成的尾部喃喃伪影修复工具。

检测每期 audio/segments/turn*.wav 的尾部伪影（主语音 + 静音间隙 + 短促咕哝），
对命中的 turn 用 use_random 重生成（最多 N 次），取干净版本，重拼接 + 变速出 episode.wav。

用法：D:/Env/Miniconda/envs/itts310/python.exe scripts/fix_mumble_indextts.py <episode_dir>
"""
import sys, json, shutil
import numpy as np
import soundfile as sf
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "_diag" / "index-tts-repo"))

MODEL_DIR = str(REPO / "models" / "indextts2")
CFG = str(REPO / "models" / "indextts2" / "config.yaml")
VS = REPO / "shows" / "vllm-podcast" / "voice-samples"
REFS = {
    "S1": str(VS / "laozhang_16k.wav"),
    "S2": str(VS / "akai_16k.wav"),
    "S3": str(VS / "azhe_16k.wav"),
}
OUT_SR = 22050
SPEED_RATE = 0.88
TARGET_RMS_DB = -17.0
MAX_GAIN_DB = 12.0
MAX_TRIES = 4


def trailing_burst(x, sr):
    n = int(0.02 * sr); m = len(x) // n
    if m < 10:
        return False
    rms = np.sqrt((x[: m * n].reshape(m, n) ** 2).mean(1) + 1e-12)
    vo = rms > 10 ** (-38 / 20); vi = np.where(vo)[0]
    if len(vi) < 5:
        return False
    g = [(vi[i - 1], vi[i], vi[i] - vi[i - 1] - 1) for i in range(1, len(vi)) if vi[i] - vi[i - 1] > 1]
    if not g:
        return False
    lge = g[-1][1]; tail = (vi >= lge).sum() * 0.02; gd = g[-1][2] * 0.02
    return gd >= 0.12 and 0.04 < tail < 0.7 and lge > m * 0.5


def main():
    ep_dir = Path(sys.argv[1]).resolve()
    ad = ep_dir / "audio"
    seg = ad / "segments"

    from scripts.script_parser import parse
    script = parse(ep_dir / "script.md")
    st = [t for t in script.turns if (t.text or "").strip()]
    pron = json.loads((REPO / "shows" / "vllm-podcast" / "season" / "pronunciation.json").read_text(encoding="utf-8"))["terms"]
    pmap = {k: v.get("replace", k) for k, v in pron.items() if v.get("replace")}
    def ap(t):
        for k, v in sorted(pmap.items(), key=lambda kv: -len(kv[0])):
            t = t.replace(k, v)
        return t

    # 检测伪影 turn
    turns = sorted(seg.glob("turn*.wav"))
    bad = []
    for w in turns:
        i = int(w.stem.replace("turn", ""))
        x, sr = sf.read(w, dtype="float32")
        if x.ndim > 1:
            x = x.mean(1)
        if trailing_burst(x, sr):
            bad.append((i, w.stem))
    print(f"[detect] {len(turns)} turns, 伪影 {len(bad)} 个: {[b[1] for b in bad]}", flush=True)
    if not bad:
        print("[ok] 无伪影，无需修复", flush=True)
        return

    from indextts.infer_v2 import IndexTTS2
    tts = IndexTTS2(cfg_path=CFG, model_dir=MODEL_DIR, use_fp16=False, device="cuda")
    fixed = 0
    for i, stem in bad:
        turn = st[i]
        ref = REFS.get(turn.speaker, REFS["S1"])
        text = ap((turn.text or "").strip())
        target = seg / f"turn{i:03d}.wav"
        shutil.copy(target, str(target) + ".bak")
        done = False
        for attempt in range(MAX_TRIES):
            tmp = seg / f"turn{i:03d}_r.wav"
            tts.infer(spk_audio_prompt=ref, text=text, output_path=str(tmp), use_random=True)
            x, sr = sf.read(tmp, dtype="float32")
            if x.ndim > 1:
                x = x.mean(1)
            if not trailing_burst(x, sr):
                shutil.move(str(tmp), str(target))
                done = True
                fixed += 1
                break
        tmp = seg / f"turn{i:03d}_r.wav"
        if tmp.exists():
            tmp.unlink()
        (Path(str(target) + ".bak")).unlink(missing_ok=True)
        print(f"  {stem}: {'修复' if done else '重试多次仍有伪影，保留原样'}", flush=True)

    # 重拼接 + 响度归一化 + 变速
    print("[concat] 重拼接 + 处理 ...", flush=True)
    import librosa, subprocess
    parts = []
    gap = np.zeros(int(0.1 * OUT_SR), dtype="float32")
    for w in sorted(seg.glob("turn*.wav")):
        x, sr = sf.read(w, dtype="float32")
        if x.ndim > 1:
            x = x.mean(1)
        if sr != OUT_SR:
            x = librosa.resample(x, orig_sr=sr, target_sr=OUT_SR)
        rms = float(np.sqrt((x ** 2).mean()) + 1e-9)
        g = min(TARGET_RMS_DB - 20 * np.log10(rms), MAX_GAIN_DB)
        x = x * (10 ** (g / 20))
        pk = float(np.abs(x).max())
        if pk > 0.95:
            x = x * (0.95 / pk)
        parts.append(x)
        parts.append(gap)
    out = np.concatenate(parts[:-1])
    pk = float(np.abs(out).max())
    if pk > 0.95:
        out = out * (0.95 / pk)
    raw = ad / "_raw.wav"
    sf.write(raw, out, OUT_SR)
    subprocess.run(["ffmpeg", "-y", "-i", str(raw), "-filter:a", f"atempo={SPEED_RATE}", str(ad / "episode.wav")],
                   check=True, capture_output=True)
    raw.unlink(missing_ok=True)
    fx, fsr = sf.read(str(ad / "episode.wav"))
    print(f"[done] 修复 {fixed}/{len(bad)} 处 → episode.wav {len(fx)/fsr:.0f}s @ {fsr}Hz", flush=True)


if __name__ == "__main__":
    main()
