#!/usr/bin/env python3
"""TTS 正式方案：IndexTTS-2 单句合成（2026-08-08 定案）。

逐 turn 独立生成，无跨 turn 上下文累积 —— 解决 FireRed 逐段/carryover 合成的
尾部喃喃伪影（ep01 实测 16 处 → IndexTTS-2 仅 4 处且可重生成修复）。

环境：conda env `itts310`（Python 3.10 + torch 2.8.0+cu128）。
用法：
    D:/Env/Miniconda/envs/itts310/python.exe scripts/indextts_synth_singleturn.py <episode_dir>
产物：<episode_dir>/audio/episode.wav + segments/turn*.wav
"""
import sys, time, json
import numpy as np
import soundfile as sf
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))  # 让 `from scripts.script_parser import ...` 可用
sys.path.insert(0, str(REPO / "_diag" / "index-tts-repo"))

MODEL_DIR = str(REPO / "models" / "indextts2")
CFG = str(REPO / "models" / "indextts2" / "config.yaml")
VS = REPO / "shows" / "vllm-podcast" / "voice-samples"

# IndexTTS2 用 16kHz mono 参考（已预转好）
REFS = {
    "S1": str(VS / "laozhang_16k.wav"),
    "S2": str(VS / "akai_16k.wav"),
}
OUT_SR = 22050  # IndexTTS2 BigVGAN v2 输出采样率


def load_pronunciation():
    pron = REPO / "shows" / "vllm-podcast" / "season" / "pronunciation.json"
    if not pron.exists():
        return {}
    d = json.loads(pron.read_text(encoding="utf-8"))
    return {k: v.get("replace", k) for k, v in d.get("terms", {}).items() if v.get("replace")}


def apply_pron(text, pron_map):
    for term, pron in sorted(pron_map.items(), key=lambda kv: -len(kv[0])):
        text = text.replace(term, pron)
    return text


def main():
    if len(sys.argv) < 2:
        raise SystemExit("用法: indextts_synth_singleturn.py <episode_dir>")
    ep_dir = Path(sys.argv[1]).resolve()
    script_md = ep_dir / "script.md"

    from scripts.script_parser import parse
    script = parse(script_md)
    turns = [t for t in script.turns if (t.text or "").strip()]
    pron_map = load_pronunciation()
    print(f"[prep] {len(turns)} turns, {len(pron_map)} 发音替换规则", flush=True)

    ad = ep_dir / "audio"
    seg = ad / "segments"
    seg.mkdir(parents=True, exist_ok=True)
    # 清理旧产物（FireRed 逐段残留 chunk + 旧 turn + 旧 episode）
    for f in seg.glob("turn*.wav"):
        f.unlink()
    for f in seg.glob("chunk*.wav"):
        f.unlink()
    for f in ad.glob("chunk*.wav"):
        f.unlink()

    print("[load] IndexTTS2 ...", flush=True)
    t0 = time.time()
    from indextts.infer_v2 import IndexTTS2
    tts = IndexTTS2(cfg_path=CFG, model_dir=MODEL_DIR, use_fp16=False, device="cuda")
    print(f"[load] 模型加载 {time.time()-t0:.1f}s", flush=True)

    for i, t in enumerate(turns):
        out_wav = seg / f"turn{i:03d}.wav"
        if out_wav.exists():
            continue
        text = apply_pron((t.text or "").strip(), pron_map)
        ref = REFS.get(t.speaker, REFS["S1"])
        t1 = time.time()
        tts.infer(spk_audio_prompt=ref, text=text, output_path=str(out_wav))
        print(f"turn{i:03d} [{t.speaker}] done: {time.time()-t1:.1f}s", flush=True)

    # 拼接：100ms 间隙，统一 22050Hz
    print("[concat] 拼接 ...", flush=True)
    parts = []
    gap = np.zeros(int(0.1 * OUT_SR), dtype="float32")
    for i in range(len(turns)):
        x, sr = sf.read(seg / f"turn{i:03d}.wav", dtype="float32")
        if x.ndim > 1:
            x = x.mean(1)
        if sr != OUT_SR:
            import librosa
            x = librosa.resample(x, orig_sr=sr, target_sr=OUT_SR)
        parts.append(x)
        parts.append(gap)
    out = np.concatenate(parts[:-1])
    peak = np.abs(out).max()
    if peak > 0.95:
        out = out * (0.95 / peak)
    full = ad / "episode.wav"
    sf.write(full, out, OUT_SR)
    print(f"[done] episode.wav {len(out)/OUT_SR:.1f}s @ {OUT_SR}Hz", flush=True)


if __name__ == "__main__":
    main()
