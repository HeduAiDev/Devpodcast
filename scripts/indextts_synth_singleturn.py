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
    "S1": str(VS / "laozhang_16k.wav"),   # 老张（主持人）
    "S2": str(VS / "akai_16k.wav"),       # 阿凯（作者/技术大佬）
    "S3": str(VS / "azhe_16k.wav"),       # 阿哲（北京话主持人，Qwen dylan 克隆）——读者代言人
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
        ref = REFS.get(t.speaker, REFS["S1"])
        t1 = time.time()
        # turn 内 <break Nms> 拆片段：逐段合成 + 插静音（修断句连读）
        segs = t.segments if getattr(t, "segments", None) else [((t.text or "").strip(), None)]
        seg_audios = []
        for seg_text, seg_pause in segs:
            st = apply_pron(seg_text.strip(), pron_map)
            if not st:
                continue
            tmp = seg / f"_part{i:03d}_{len(seg_audios)}.wav"
            tts.infer(spk_audio_prompt=ref, text=st, output_path=str(tmp))
            x, sr = sf.read(str(tmp), dtype="float32")
            if x.ndim > 1:
                x = x.mean(1)
            seg_audios.append((x, sr, seg_pause))
            tmp.unlink()
        if seg_audios:
            target_sr = seg_audios[0][1]
            merged = []
            for x, sr, pause in seg_audios:
                merged.append(x)
                if pause:
                    merged.append(np.zeros(int(sr * pause / 1000), dtype="float32"))
            audio = np.concatenate(merged)
            sf.write(str(out_wav), audio, target_sr)
        print(f"turn{i:03d} [{t.speaker}] done: {time.time()-t1:.1f}s ({len(seg_audios)} 段)", flush=True)

    # 处理：逐 turn 响度归一化（修阿哲音量低）→ 拼接 → ffmpeg atempo 变速降速（修语速快）
    # 注意：变速用 ffmpeg atempo（WSOLA，保调无回音），绝不用 librosa time_stretch（相位声码器产生回音/发散）
    import librosa
    SPEED_RATE = 0.88       # 0.88x ≈ 降速 12%
    TARGET_RMS_DB = -17.0   # 目标响度（dB）
    MAX_GAIN_DB = 12.0      # 单 turn 最大增益（防过度放大底噪）
    FFMPEG = "ffmpeg"
    print(f"[proc] 响度归一化到 {TARGET_RMS_DB}dB + 变速 {SPEED_RATE}x (ffmpeg atempo)", flush=True)

    print("[concat] 拼接（响度归一化）...", flush=True)
    parts = []
    gap = np.zeros(int(0.1 * OUT_SR), dtype="float32")
    for i in range(len(turns)):
        x, sr = sf.read(seg / f"turn{i:03d}.wav", dtype="float32")
        if x.ndim > 1:
            x = x.mean(1)
        if sr != OUT_SR:
            x = librosa.resample(x, orig_sr=sr, target_sr=OUT_SR)
        # 响度归一化（RMS 拉到目标，限增益）
        rms = float(np.sqrt((x ** 2).mean()) + 1e-9)
        cur_db = 20 * np.log10(rms)
        gain_db = min(TARGET_RMS_DB - cur_db, MAX_GAIN_DB)
        x = x * (10 ** (gain_db / 20))
        pk = float(np.abs(x).max())
        if pk > 0.95:
            x = x * (0.95 / pk)
        parts.append(x)
        parts.append(gap)
    out = np.concatenate(parts[:-1])
    peak = np.abs(out).max()
    if peak > 0.95:
        out = out * (0.95 / peak)
    raw = ad / "_raw_loudnorm.wav"
    sf.write(raw, out, OUT_SR)

    # ffmpeg atempo 变速降速（专业 WSOLA 算法，保调无回音）
    import subprocess
    final = ad / "episode.wav"
    subprocess.run([FFMPEG, "-y", "-i", str(raw), "-filter:a", f"atempo={SPEED_RATE}", str(final)],
                   check=True, capture_output=True)
    raw.unlink(missing_ok=True)
    import soundfile as _sf
    fx, fsr = _sf.read(str(final), dtype="float32")
    print(f"[done] episode.wav {len(fx)/fsr:.1f}s @ {fsr}Hz (变速 {SPEED_RATE}x)", flush=True)


if __name__ == "__main__":
    main()
