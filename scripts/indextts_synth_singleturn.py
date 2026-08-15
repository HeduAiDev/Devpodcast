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

# 主方案：IndexTTS-2.5（G2P 注音，支持 {{em}} 重读词的发音控制）；2 为 fallback
MODEL_DIR_25 = str(REPO / "models" / "indextts2_5")
CFG_25 = str(REPO / "models" / "indextts2_5" / "config.yaml")
MODEL_DIR = str(REPO / "models" / "indextts2")
CFG = str(REPO / "models" / "indextts2" / "config.yaml")
EM_SLOW_RATE = 0.97  # {{em}} 重读段放慢幅度（2026-08-13 用户定档：放慢 3%）
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


# 图记号孤立单字母：IndexTTS 把大写 S 和小写 s 都读成 /es/，无法区分能指(S)与所指(s)。
# 合成前文本处理：孤立 S→「大写 S」、孤立 s→「小写 s」；已带「大写/小写/大/小」前缀的跳过。
# 只处理 S/s（B 站、说话人 A/B 等不受影响）。
_S_PREFIX_RE = re.compile(r"(大写|小写|大|小)(的)?\s*[Ss]")
_S_ISOLATED_RE = re.compile(r"(?<![A-Za-z0-9])S(?![A-Za-z0-9])")
_s_ISOLATED_RE = re.compile(r"(?<![A-Za-z0-9])s(?![A-Za-z0-9])")


def mark_letter_marks(text: str) -> str:
    """把孤立的图记号 S/s 展开为「大写 S/小写 s」（发音表替换产物里的 S 也会展开，
    如「S 到 S 一撇」→「大写 S 到大写 S 一撇」，听感更明确）。"""
    ph: list[str] = []
    def _keep(m):
        ph.append(m.group(0))
        return f"\x01{len(ph) - 1}\x01"
    text = _S_PREFIX_RE.sub(_keep, text)          # 保护已有大小写描述的
    text = _S_ISOLATED_RE.sub("大写 S", text)
    text = _s_ISOLATED_RE.sub("小写 s", text)
    text = re.sub(r"\x01(\d+)\x01", lambda m: ph[int(m.group(1))], text)
    return text


def load_g2p(ep_dir: Path | None = None):
    """发音表的 g2p 注音字段（IndexTTS-2.5 专用）：{term: "<它思|TA1 SI1>"}。
    只在 {{em}} 重读段生效——writer 标 {{em}}，注音由发音表维护。"""
    if ep_dir is not None:
        show_dir = Path(ep_dir).resolve().parent.parent
        pron = show_dir / "season" / "pronunciation.json"
    else:
        pron = REPO / "shows" / "vllm-podcast" / "season" / "pronunciation.json"
    if not pron.exists():
        return {}
    d = json.loads(pron.read_text(encoding="utf-8"))
    return {k: v["g2p"] for k, v in d.get("terms", {}).items() if v.get("g2p")}


def clean_for_speech(text):
    """口播清洗（从博客管线移植，writer 写法规范的合成侧兜底）：
    1) 删「全角括号内无中文」的注释——「凝缩（condensation）」→「凝缩」；
       半角 ( ) 是图记号一部分（s(A)、i(a)），绝不删。
    2) 删全角括号开头的拉丁前缀——「（signifiant de l'Autre——大他者的能指」→「（大他者的能指」；
       数字开头不删（「（1957 年…」保留）。"""
    text = re.sub(r"_+", "……", text)  # 填空下划线 → 省略号（500ms 停顿示意留白，防模型乱读，2026-08-13）
    # 直角引号整体剥除（2026-08-15 用户定案）：引号在语音里不出声，紧贴标点会读成怪音
    # （"「随便」，"→"随便塞"，2026-08-14 插空格补丁只救了 5 种组合，"」："等 149 处仍漏）。
    # script.md 稿面保留引号，仅合成侧剥离。
    text = re.sub(r"[「」『』]", "", text)
    text = re.sub(r"（[^（）一-鿿]*）", "", text)
    text = re.sub(
        r"（(?:[^一-鿿，。；、！？「」…——0-9]+?)(?:——|—|，|,|；)?(?=[一-鿿「」『』《》0-9]|$)",
        "（", text)
    return text


def main():
    # 强制 UTF-8 stdout：infer_v2_5 内部会 print 文本，含法语字符时 GBK 控制台会崩（2026-08-13）
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) < 2:
        raise SystemExit("用法: indextts_synth_singleturn.py <episode_dir>")
    ep_dir = Path(sys.argv[1]).resolve()
    script_md = ep_dir / "script.md"

    from scripts.script_parser import parse
    script = parse(script_md)
    turns = [t for t in script.turns if (t.text or "").strip()]
    pron_map = load_pronunciation(ep_dir)
    g2p_map = load_g2p(ep_dir)
    print(f"[prep] {len(turns)} turns, {len(pron_map)} 发音替换规则, {len(g2p_map)} g2p 注音", flush=True)

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

    import subprocess
    print("[load] IndexTTS2.5 ...", flush=True)
    t0 = time.time()
    g2p_ok = False
    try:
        from indextts.infer_v2_5 import IndexTTS2
        tts = IndexTTS2(cfg_path=CFG_25, model_dir=MODEL_DIR_25, use_bf16=False,
                        device="cuda", use_qwen_emo=True)
        g2p_ok = True
    except Exception as e:
        print(f"[load] IndexTTS-2.5 不可用（{e}），回退 IndexTTS-2"
              f"（{{em}} 仅放慢+响度，无 G2P 注音）", flush=True)
        from indextts.infer_v2 import IndexTTS2
        tts = IndexTTS2(cfg_path=CFG, model_dir=MODEL_DIR, use_fp16=False, device="cuda")
    print(f"[load] 模型加载 {time.time()-t0:.1f}s (g2p={'on' if g2p_ok else 'off'})", flush=True)
    FFMPEG = "ffmpeg"

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

        def _is_emph(txt):
            return any(term in txt for term in t.em_terms)

        # 护栏：把过短片段并入后一段（其 pause 也带走）；含 {{em}} 词的片段豁免（必须独立成段）
        merged_segs = []
        for txt, pause in raw_segs:
            if (merged_segs and len(txt.strip()) < MIN_SEG_CHARS
                    and not _is_emph(txt) and not _is_emph(merged_segs[-1][0])):
                # 太短 → 并到上一段末尾（pause 顺延）
                ptxt, ppause = merged_segs[-1]
                merged_segs[-1] = (ptxt + txt, pause if pause is not None else ppause)
            else:
                merged_segs.append((txt, pause))
        # 逐段合成 + 剪边 + 按 pause 插静音
        # g2p 注音全局生效（发音表有注音的词都注音——读准问题）；{{em}} 段额外放慢+响度（重读问题）
        seg_clips = []
        prev_rms_db = None
        for txt, pause in merged_segs:
            st = apply_pron(clean_for_speech(txt.strip()), pron_map)
            if not st:
                continue
            st = mark_letter_marks(st)  # 图记号 S/s 大小写区分（2026-08-13）
            emph = _is_emph(txt)
            if g2p_ok:
                for term in sorted(g2p_map, key=lambda x: -len(x)):
                    if term in st:
                        st = st.replace(term, g2p_map[term])
            tmp = seg / f"_brk{i:03d}_{len(seg_clips)}.wav"
            kw = dict(spk_audio_prompt=ref, text=st, output_path=str(tmp))
            if g2p_ok:
                kw["lang"] = "ZH"
            tts.infer(**kw)
            x, sr = sf.read(str(tmp), dtype="float32")
            if x.ndim > 1:
                x = x.mean(1)
            x = _trim_edges(x, sr)
            if emph:
                x = atempo(x, sr, EM_SLOW_RATE)  # 放慢 3%（WSOLA 保调，重读时长成分）
                rms = float(np.sqrt((x ** 2).mean()) + 1e-9)
                cur_db = 20 * np.log10(rms)
                if prev_rms_db is not None:
                    g = 10 ** ((prev_rms_db - cur_db) / 20)  # 响度对齐前段（0dB 梯度）
                    x = np.clip(x * g, -1.0, 1.0)
            prev_rms_db = 20 * np.log10(float(np.sqrt((x ** 2).mean()) + 1e-9))
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
    import librosa
    # 2026-08-13 用户定档:全角色原速(1.0)——0.88/0.92 降速产生"人机感"。
    # atempo 保留机制:以后如需微调,只改这里。
    SPEED = {"S1": 1.0, "S2": 1.0, "S3": 1.0}
    DEFAULT_SPEED = 1.0
    TARGET_RMS_DB = -17.0   # 目标响度（dB）
    MAX_GAIN_DB = 12.0      # 单 turn 最大增益（防过度放大底噪）
    print(f"[proc] 响度归一化到 {TARGET_RMS_DB}dB + 按角色变速 {SPEED}", flush=True)

    print("[concat] 拼接（响度归一化 + 按角色变速）...", flush=True)
    parts = []
    gap = np.zeros(int(0.3 * OUT_SR), dtype="float32")  # turn 间 300ms（2026-08-11 主线定档：换人气口/前调感；08-15 移植）
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
