#!/usr/bin/env python3
"""TTS 正式方案：IndexTTS-2 单句合成（2026-08-08 定案）。

逐 turn 独立生成，无跨 turn 上下文累积 —— 解决 FireRed 逐段/carryover 合成的
尾部喃喃伪影（ep01 实测 16 处 → IndexTTS-2 仅 4 处且可重生成修复）。

环境：conda env `itts310`（Python 3.10 + torch 2.8.0+cu128）。
用法：
    D:/miniconda3/envs/itts310/python.exe scripts/indextts_synth_singleturn.py <episode_dir>
产物：<episode_dir>/audio/episode.wav + segments/turn*.wav
"""
import sys, time, json
import re
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


def load_pronunciation(ep_dir: Path | None = None):
    """按节目取发音表：<show>/season/pronunciation.json（show = ep_dir 的上两级）。
    不传 ep_dir 时回退 vllm-podcast（历史默认）。"""
    if ep_dir is not None:
        show_dir = Path(ep_dir).resolve().parent.parent
        pron = show_dir / "season" / "pronunciation.json"
    else:
        pron = REPO / "shows" / "vllm-podcast" / "season" / "pronunciation.json"
    if not pron.exists():
        return {}
    d = json.loads(pron.read_text(encoding="utf-8"))
    return {k: v.get("replace", k) for k, v in d.get("terms", {}).items() if v.get("replace")}


def apply_pron(text, pron_map):
    for term, pron in sorted(pron_map.items(), key=lambda kv: -len(kv[0])):
        text = text.replace(term, pron)
    return text


def clean_for_speech(text):
    """口播清洗（从博客管线移植，writer 写法规范的合成侧兜底）：
    1) 删「全角括号内无中文」的注释——「凝缩（condensation）」→「凝缩」；
       半角 ( ) 是图记号一部分（s(A)、i(a)），绝不删。
    2) 删全角括号开头的拉丁前缀——「（signifiant de l'Autre——大他者的能指」→「（大他者的能指」；
       数字开头不删（「（1957 年…」保留）。"""
    text = re.sub(r"（[^（）一-鿿]*）", "", text)
    text = re.sub(
        r"（(?:[^一-鿿，。；、！？「」…——0-9]+?)(?:——|—|，|,|；)?(?=[一-鿿「」『』《》0-9]|$)",
        "（", text)
    return text


def main():
    if len(sys.argv) < 2:
        raise SystemExit("用法: indextts_synth_singleturn.py <episode_dir>")
    ep_dir = Path(sys.argv[1]).resolve()
    script_md = ep_dir / "script.md"

    from scripts.script_parser import parse
    script = parse(script_md)
    turns = [t for t in script.turns if (t.text or "").strip()]
    pron_map = load_pronunciation(ep_dir)
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

    # <break Nms> 拆段合成（确定性停顿）。IndexTTS 标点停顿是随机的（句号 0.24s vs 0.02s 不稳定），
    # 可靠的停顿只能拆段插静音。但拆段会把短片段拉长（「好问题。」→「好~问题」），所以：
    #   1. 长度护栏——片段 <14 字就并进相邻段（不孤立短片段）
    #   2. 每段先剪首尾静音再插精确时长——停顿可控（不会因片段自带边缘静音叠加而偏长）
    MIN_SEG_CHARS = 14
    SIL_DB = 10 ** (-45 / 20)
    TRIM_PAD_MS = 50  # _trim_edges 两边各保留的垫片，插静音时扣掉避免叠加

    def _trim_edges(x, sr):
        n = int(0.02 * sr); m = len(x) // n
        if m < 3:
            return x
        rms = np.sqrt((x[: m * n].reshape(m, n) ** 2).mean(1) + 1e-12)
        voiced = rms > SIL_DB
        idx = np.where(voiced)[0]
        if len(idx) == 0:
            return x
        pad = int(TRIM_PAD_MS / 1000 * sr)
        a = max(0, idx[0] * n - pad)
        b = min(len(x), (idx[-1] + 1) * n + pad)
        return x[a:b]

    for i, t in enumerate(turns):
        out_wav = seg / f"turn{i:03d}.wav"
        if out_wav.exists():
            continue
        ref = REFS.get(t.speaker, REFS["S1"])
        t1 = time.time()
        # 按 <break Nms> 切片段 + 长度护栏
        raw_segs = t.segments if getattr(t, "segments", None) else [((t.text or "").strip(), None)]
        # 护栏：把过短片段并入后一段（其 pause 也带走）
        merged_segs = []
        for txt, pause in raw_segs:
            if merged_segs and len(txt.strip()) < MIN_SEG_CHARS and merged_segs:
                # 太短 → 并到上一段末尾（pause 顺延）
                ptxt, ppause = merged_segs[-1]
                merged_segs[-1] = (ptxt + txt, pause if pause is not None else ppause)
            else:
                merged_segs.append((txt, pause))
        # 逐段合成 + 剪边 + 按 pause 插静音
        seg_clips = []
        for txt, pause in merged_segs:
            st = apply_pron(clean_for_speech(txt.strip()), pron_map)
            if not st:
                continue
            tmp = seg / f"_brk{i:03d}_{len(seg_clips)}.wav"
            tts.infer(spk_audio_prompt=ref, text=st, output_path=str(tmp))
            x, sr = sf.read(str(tmp), dtype="float32")
            if x.ndim > 1:
                x = x.mean(1)
            x = _trim_edges(x, sr)
            seg_clips.append((x, sr, pause))
            tmp.unlink()
        if seg_clips:
            tsr = seg_clips[0][1]
            merged = []
            for x, sr, pause in seg_clips:
                merged.append(x)
                if pause:
                    # 扣掉 trim 两边各留的 50ms 垫片——接缝总静音才等于请求值
                    # （不剪更狠：削掉尾音辅音会发闷）
                    net = max(0, pause - 2 * TRIM_PAD_MS)
                    merged.append(np.zeros(int(sr * net / 1000), dtype="float32"))
            audio = np.concatenate(merged)
            sf.write(str(out_wav), audio, tsr)
        print(f"turn{i:03d} [{t.speaker}] done: {time.time()-t1:.1f}s ({len(seg_clips)} 段)", flush=True)

    # 处理：逐 turn 响度归一化（修阿哲音量低）+ 按角色变速 → 拼接
    # 注意：变速用 ffmpeg atempo（WSOLA，保调无回音），绝不用 librosa time_stretch（相位声码器产生回音/发散）
    # 语速按角色分开：阿凯换 Aiden 参考后本身已慢（4.5 字/秒），不再降速；老张/阿哲维持原 0.88。
    import librosa, subprocess
    SPEED = {"S1": 0.88, "S2": 0.92, "S3": 0.88}
    DEFAULT_SPEED = 0.88
    TARGET_RMS_DB = -17.0   # 目标响度（dB）
    MAX_GAIN_DB = 12.0      # 单 turn 最大增益（防过度放大底噪）
    FFMPEG = "ffmpeg"
    print(f"[proc] 响度归一化到 {TARGET_RMS_DB}dB + 按角色变速 {SPEED}", flush=True)

    def atempo(x, sr, rate):
        """ffmpeg atempo 变速（WSOLA 保调）。rate=1.0 直接返回。"""
        if abs(rate - 1.0) < 1e-6:
            return x
        ti, to = ad / "_sp_in.wav", ad / "_sp_out.wav"
        sf.write(ti, x, sr)
        subprocess.run([FFMPEG, "-y", "-i", str(ti), "-filter:a", f"atempo={rate}", str(to)],
                       check=True, capture_output=True)
        y, _ = sf.read(str(to), dtype="float32")
        ti.unlink(missing_ok=True)
        to.unlink(missing_ok=True)
        return y.mean(1) if y.ndim > 1 else y

    print("[concat] 拼接（响度归一化 + 按角色变速）...", flush=True)
    parts = []
    gap = np.zeros(int(0.1 * OUT_SR), dtype="float32")
    for i, t in enumerate(turns):
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
        x = atempo(x, OUT_SR, SPEED.get(t.speaker, DEFAULT_SPEED))
        parts.append(x)
        parts.append(gap)
    out = np.concatenate(parts[:-1])
    peak = np.abs(out).max()
    if peak > 0.95:
        out = out * (0.95 / peak)
    final = ad / "episode.wav"
    sf.write(final, out, OUT_SR)
    print(f"[done] episode.wav {len(out)/OUT_SR:.1f}s @ {OUT_SR}Hz", flush=True)


if __name__ == "__main__":
    main()
