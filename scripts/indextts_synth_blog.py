#!/usr/bin/env python3
"""博客栏目 TTS：IndexTTS-2 单句合成（博客版，2026-08-09）。

与 indextts_synth_singleturn.py 同链（拆段护栏/剪边/插静音/响度/atempo），
但输入是 markdown 文章而非播客脚本：清洗 markdown（剔代码块/表格转口语/
删无中文的括号注释）→ 段落 turns → 单角色（S1 老张音色）朗读。

用法（生产机，itts310 环境）：
    D:/miniconda3/envs/itts310/python.exe scripts/indextts_synth_blog.py shows/lacan-desire
    D:/miniconda3/envs/itts310/python.exe scripts/indextts_synth_blog.py shows/lacan-desire --only 01
    ... --dry-run   # 无模型环境：只输出清洗+发音表后的朗读文本预览（验证用）

输入：shows/<column>/episodes/epNN-<slug>/script.md（一篇=一期）
产物：shows/<column>/episodes/epNN-<slug>/audio/episode.wav + audio/segments/NN-*_turn*.wav
发音表：shows/<column>/season/pronunciation.json
"""
import sys, time, json, re, subprocess
from pathlib import Path

# 重依赖（numpy/soundfile/librosa/IndexTTS2）在非 dry-run 路径内 import，
# 保证 --dry-run 在无模型/无依赖环境也可预览清洗+发音表效果。

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "_diag" / "index-tts-repo"))

from scripts.script_parser import auto_segment  # cut5 断句：标点自动切段 + 精确停顿（cc9a53a）

MODEL_DIR = str(REPO / "models" / "indextts2")
CFG = str(REPO / "models" / "indextts2" / "config.yaml")
VS = REPO / "shows" / "vllm-podcast" / "voice-samples"
REF_S1 = str(VS / "laozhang_16k.wav")   # 博客单角色：老张（与播客 S1 同音色）
OUT_SR = 22050
SPEED_RATE = 0.88
TARGET_RMS_DB = -17.0
MAX_GAIN_DB = 12.0
FFMPEG = "ffmpeg"

# ---------- markdown → 朗读文本 ----------

def clean_markdown(text: str) -> list[str]:
    """文章 → 朗读段落列表。返回 [(is_heading, text), ...]"""
    # 1) 剔 fenced code blocks（ASCII 图全在里面）
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    # 2) 剔 markdown 链接：保留链接文字
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    # 3) 剔行首导航（→ 下一篇 / → 系列收官）
    text = re.sub(r"(?m)^\s*→.*$", "", text)
    # 4) 表格行 → 口语（单元格 join 逗号）；分隔线行剔除
    lines = text.split("\n")
    out_lines = []
    for ln in lines:
        s = ln.strip()
        if re.match(r"^\|[\s\-:|]+\|$", s):        # |---|---| 分隔线
            continue
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            s = "，".join(cells)                    # 表格 → 连读
        out_lines.append(s)
    text = "\n".join(out_lines)
    # 5) 删「全角括号内无中文」的注释（纯外语注释朗读无意义）。
    #    注意：半角 ( ) 是图记号的一部分（s(A)、i(a)、S/s），绝不删。
    text = re.sub(r"（[^（）一-鿿]*）", "", text)
    # 6) 删全角括号开头的拉丁术语前缀（「（signifiant de l'Autre——大他者的能指效果」→「（大他者的能指效果」）。
    #    数字开头不删（「（1957 年…」保留）；分隔符（——/，/；）随前缀一并删除。
    #    注意：全角冒号「：」不在排除组——「（pulsion：ce qui…，《中文出处》」整段拉丁前缀连冒号一起吞掉。
    text = re.sub(
        r"（(?:[^一-鿿，。；、！？「」…——0-9]+?)(?:——|—|，|,|；)?(?=[一-鿿「」『』《》0-9]|$)",
        "（", text)
    # 6) 去行内标记：标题/加粗/引用/列表/围栏
    text = re.sub(r"(?m)^#{1,6}\s*", "", text)
    text = re.sub(r"\*\*", "", text)
    text = re.sub(r"(?m)^>\s*", "", text)
    text = re.sub(r"(?m)^[-*+]\s+", "", text)
    text = re.sub(r"(?m)^\d+\.\s+", "", text)
    text = text.replace("`", "")
    # 7) 段落化（空行分割），返回 [(is_heading, text)]
    paras = []
    for para in re.split(r"\n\s*\n", text):
        p = " ".join(ln.strip() for ln in para.split("\n") if ln.strip()).strip()
        if not p:
            continue
        paras.append(p)
    return paras


def load_pronunciation(column_dir: Path):
    pron = column_dir / "season" / "pronunciation.json"  # 标准 show 结构：发音表归 season/
    if not pron.exists():
        return {}
    d = json.loads(pron.read_text(encoding="utf-8"))
    return {k: v.get("replace", k) for k, v in d.get("terms", {}).items() if v.get("replace")}


def apply_pron(text: str, pron_map: dict) -> str:
    for term, pron in sorted(pron_map.items(), key=lambda kv: -len(kv[0])):
        text = text.replace(term, pron)
    return text


def build_turns(paras, pron_map):
    """段落 → script turns：[(speaker, text)]。标题段前后加停顿。"""
    turns = []
    for p in paras:
        p = apply_pron(p, pron_map).strip()
        if not p:
            continue
        turns.append(("S1", p))
    return turns


# ---------- 合成链（同 singleturn） ----------

MIN_SEG_CHARS = 14
SIL_DB = 10 ** (-45 / 20)


def _trim_edges(x, sr):
    n = int(0.02 * sr); m = len(x) // n
    if m < 3:
        return x
    rms = np.sqrt((x[: m * n].reshape(m, n) ** 2).mean(1) + 1e-12)
    voiced = rms > SIL_DB
    idx = np.where(voiced)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] * n - int(0.05 * sr))
    b = min(len(x), (idx[-1] + 1) * n + int(0.05 * sr))
    return x[a:b]


def main():
    global np, sf
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    if len(sys.argv) < 2:
        raise SystemExit("用法: indextts_synth_blog.py <column_dir> [--only NN] [--dry-run]")
    column = Path(sys.argv[1]).resolve()
    only = None
    dry = "--dry-run" in sys.argv
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]

    # 标准 show 结构：一篇 = 一期 episodes/epNN-<slug>/script.md
    posts = sorted(column.glob("episodes/*/script.md"))
    if only:
        posts = [p for p in posts if p.parent.name.startswith(f"ep{only.zfill(2)}-")]
    if not posts:
        raise SystemExit(f"没有找到文章: {column}/episodes/*/script.md（--only 按期号前缀匹配，如 --only 01）")

    pron_map = load_pronunciation(column)
    print(f"[prep] {len(posts)} 篇, {len(pron_map)} 发音规则, 参考音色 {Path(REF_S1).name}", flush=True)

    if dry:
        for pmd in posts:
            paras = clean_markdown(pmd.read_text(encoding="utf-8"))
            turns = build_turns(paras, pron_map)
            print(f"--- {pmd.parent.name}: {len(paras)} 段 → {len(turns)} turn ---", flush=True)
            for spk, t in turns:
                print(f"[{spk}] {t}", flush=True)
        print("[dry-run] 仅预览，未合成。")
        return

    import numpy as np, soundfile as sf  # 正式合成才需要重依赖

    for pi, pmd in enumerate(posts):
        slug = pmd.parent.name[2:]  # ep01-concepts-language → 01-concepts-language（segments 命名用）
        ad = pmd.parent / "audio"
        seg = ad / "segments"
        seg.mkdir(parents=True, exist_ok=True)
        out_wav = ad / "episode.wav"
        paras = clean_markdown(pmd.read_text(encoding="utf-8"))
        turns = build_turns(paras, pron_map)
        print(f"--- {pmd.parent.name}: {len(paras)} 段 → {len(turns)} turn ---", flush=True)
        if out_wav.exists():
            print(f"[skip] {out_wav.name} 已存在（删掉可重合成）", flush=True)
            continue

        # 加载模型（每篇一次性加载，第一篇加载最慢）
        if pi == 0 or not globals().get("tts"):
            print("[load] IndexTTS2 ...", flush=True)
            t0 = time.time()
            from indextts.infer_v2 import IndexTTS2
            globals()["tts"] = IndexTTS2(cfg_path=CFG, model_dir=MODEL_DIR, use_fp16=True, device="cuda")
            print(f"[load] 模型加载 {time.time()-t0:.1f}s", flush=True)
        tts = globals()["tts"]

        # 逐 turn 合成：cut5 断句（auto_segment 按标点切段 + 手动插精确静音）。
        # IndexTTS 标点停顿随机（句号实测 0/60/270ms 三种），抢在模型之前切开、
        # 由合成器插静音——句末 350ms / 分号 250ms / 逗号 200(≥20字) / 顿号 150ms / 省略号 400ms / 破折号 250ms。
        TRIM_PAD_MS = 50  # _trim_edges 两边各保留的垫片，插静音时扣掉避免叠加
        turn_wavs = []
        t_total = 0.0
        for i, (spk, text) in enumerate(turns):
            raw_segs = auto_segment(text, None)  # 按标点细分（清洗期已移除 <break>）
            # 护栏：过短片段并进后一段（短片段孤立合成会被拉长）
            segs = []
            for stxt, pause in raw_segs:
                if segs and len(stxt.strip()) < MIN_SEG_CHARS:
                    ptxt, ppause = segs[-1]
                    segs[-1] = (ptxt + stxt, pause if pause is not None else ppause)
                else:
                    segs.append((stxt, pause))
            seg_clips = []
            for si, (stxt, pause) in enumerate(segs):
                tmp = seg / f"_{slug}_{i:03d}_{si}_brk.wav"
                t0 = time.time()
                tts.infer(spk_audio_prompt=REF_S1, text=stxt, output_path=str(tmp))
                x, sr = sf.read(str(tmp), dtype="float32")
                if x.ndim > 1:
                    x = x.mean(1)
                x = _trim_edges(x, sr)
                seg_clips.append((x, sr, pause))
                tmp.unlink(missing_ok=True)
            if seg_clips:
                tsr = seg_clips[0][1]
                merged = []
                for x, sr, pause in seg_clips:
                    merged.append(x)
                    if pause:
                        # 扣掉 trim 两边各留的 50ms 垫片——接缝总静音才等于请求值
                        net = max(0, pause - 2 * TRIM_PAD_MS)
                        merged.append(np.zeros(int(sr * net / 1000), dtype="float32"))
                audio = np.concatenate(merged)
                out_turn = seg / f"{slug}_turn{i:03d}.wav"
                sf.write(str(out_turn), audio, tsr)
                turn_wavs.append((out_turn, tsr))
            t_total += time.time() - t0
            print(f"  turn{i:03d}/{len(turns)} ({len(text)}字→{len(segs)}段) {time.time()-t0:.1f}s", flush=True)

        # 拼接 + 响度归一化 + atempo 变速（同 singleturn）
        import librosa
        print(f"[concat] {len(turn_wavs)} turns, 响度 → {TARGET_RMS_DB}dB, 变速 {SPEED_RATE}x", flush=True)
        parts = []
        gap = np.zeros(int(0.1 * OUT_SR), dtype="float32")
        for f, sr in turn_wavs:
            x, srx = sf.read(str(f), dtype="float32")
            if x.ndim > 1:
                x = x.mean(1)
            if srx != OUT_SR:
                x = librosa.resample(x, orig_sr=srx, target_sr=OUT_SR)
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
        subprocess.run([FFMPEG, "-y", "-i", str(raw), "-filter:a", f"atempo={SPEED_RATE}", str(out_wav)],
                       check=True, capture_output=True)
        raw.unlink(missing_ok=True)
        fx, fsr = sf.read(str(out_wav), dtype="float32")
        print(f"[done] {out_wav.name} {len(fx)/fsr:.1f}s @ {fsr}Hz", flush=True)

    if dry:
        print("[dry-run] 仅预览，未合成。")


if __name__ == "__main__":
    main()
